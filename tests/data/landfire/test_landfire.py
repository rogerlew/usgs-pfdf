from unittest.mock import patch

import numpy as np
import pytest

from pfdf.data.landfire import _landfire
from pfdf.errors import DataAPIError, InvalidLFPSJobError, LFPSJobTimeoutError
from pfdf.projection import Transform
from pfdf.raster import Raster

#####
# Fixtures
#####


def check_status_mock(mock):
    mock.assert_called_with(
        "https://lfps.usgs.gov/api/job/status",
        params={"JobId": "12345"},
        timeout=10,
    )


@pytest.fixture
def download_url():
    return "https://lfps.usgs.gov/arcgis/rest/directories/arcgisjobs/landfireproductservice_gpserver/12345/scratch/12345.zip"


@pytest.fixture
def completed_job(download_url):
    return {
        "jobId": "12345",
        "status": "Succeeded",
        "outputFile": download_url,
    }


@pytest.fixture
def job_raster(tmp_path):
    "The raster file in a downloaded job"

    # Build the job folder
    raw = tmp_path / "raw"
    raw.mkdir()

    # Build a geotiff
    a = np.arange(100).reshape(10, 10)
    a = Raster.from_array(a, crs=26911, transform=(10, -10, 0, 0))
    path = raw / "12345.tif"
    a.save(path)
    return path


@pytest.fixture
def zip_data(tmp_path, zip_response, job_raster):
    files = {
        "12345.tif": job_raster,
        "12345.xml": "An XML metadata file in the job",
    }
    return zip_response(tmp_path, files)


@pytest.fixture
def zip_vector(tmp_path, zip_response):
    files = {
        "12345.shp": "A downloaded vector dataset",
        "12345.xml": "An XML metadata file in the job",
    }
    return zip_response(tmp_path, files)


@pytest.fixture
def download_mock(json_response, completed_job, zip_data):
    "Returns a function that mocks requests.get for downloading files"

    def download_mock(url, *args, **kwargs):
        "Mocks requests.get for downloading files"

        # Job submission
        if url == "https://lfps.usgs.gov/api/job/submit":
            return json_response({"jobId": "12345", "jobStatus": "esriJobSubmitted"})

        # Job completion
        elif url.startswith("https://lfps.usgs.gov/api/job/status"):
            return json_response(completed_job)

        # File download
        elif url == completed_job["outputFile"]:
            return zip_data

    return download_mock


@pytest.fixture
def timeout_mock(json_response):
    "Returns a function used to mock requests.get for timed out jobs"

    def timeout_mock(url, *args, **kwargs):

        # Job submission
        if url == "https://lfps.usgs.gov/api/job/submit":
            return json_response({"jobId": "12345", "status": "Submitted"})

        # Job never finishes
        elif url.startswith("https://lfps.usgs.gov/api/job/status"):
            return json_response({"jobId": "12345", "status": "Executing"})

    return timeout_mock


@pytest.fixture
def vector_mock(json_response, completed_job, zip_vector):
    "Returns a function that mocks requests.get for downloading files"

    def vector_mock(url, *args, **kwargs):
        "Mocks requests.get for downloading vector files"

        # Job submission
        if url == "https://lfps.usgs.gov/api/job/submit":
            return json_response({"jobId": "12345", "status": "Submitted"})

        # Job completion
        elif url.startswith("https://lfps.usgs.gov/api/job/status"):
            return json_response(completed_job)

        # File download
        elif url == completed_job["outputFile"]:
            return zip_vector

    return vector_mock


#####
# Utilities
#####


class TestCheckStatus:
    @pytest.mark.parametrize("status", ("Pending", "Executing"))
    def test_running(_, status):
        assert _landfire._check_status("12345", status) == False

    def test_succeeded(_):
        assert _landfire._check_status("12345", "Succeeded") == True

    def test_cancelled(_, assert_contains):
        with pytest.raises(InvalidLFPSJobError) as error:
            _landfire._check_status("12345", "Canceled")
        assert_contains(
            error, "Cannot download job 12345 because the job was cancelled"
        )

    def test_failed(_, assert_contains):
        with pytest.raises(InvalidLFPSJobError) as error:
            _landfire._check_status("12345", "Failed")
        assert_contains(error, "Cannot download job 12345 because the job failed")

    def test_unrecognized(_, assert_contains):
        with pytest.raises(DataAPIError) as error:
            _landfire._check_status("12345", "Unknown Status")
        assert_contains(
            error,
            "LANDFIRE LFPS returned an unrecognized status code: Unknown Status",
        )


class TestExecuteJob:
    @patch("requests.get")
    def test_success(_, mock, json_response):
        running = {"jobId": "12345", "status": "Executing"}
        finished = {
            "jobId": "12345",
            "status": "Succeeded",
            "outputFile": "https://some-file.zip",
        }
        responses = [json_response(status) for status in [running] * 3 + [finished]]
        mock.side_effect = responses

        output = _landfire._execute_job("12345", 15, 0.1, 10)
        assert output == "https://some-file.zip"
        check_status_mock(mock)

    @patch("requests.get")
    def test_failed(_, mock, json_response, assert_contains):
        running = {"jobId": "12345", "status": "Executing"}
        failed = {"jobId": "12345", "status": "Failed"}
        responses = [json_response(status) for status in [running] * 3 + [failed]]
        mock.side_effect = responses

        with pytest.raises(InvalidLFPSJobError) as error:
            _landfire._execute_job("12345", 15, 0.1, 10)
        assert_contains(error, "Cannot download job 12345 because the job failed")
        check_status_mock(mock)

    @patch("requests.get")
    def test_timed_out(_, mock, json_response, assert_contains):
        running = {"jobId": "12345", "status": "Executing"}
        responses = [json_response(running)] * 5
        mock.side_effect = responses

        with pytest.raises(LFPSJobTimeoutError) as error:
            _landfire._execute_job(
                "12345", max_job_time=0.4, refresh_rate=0.1, timeout=10
            )
        assert_contains(error, "LANDFIRE LFPS took too long to process job 12345")
        check_status_mock(mock)


#####
# Main
#####


class TestDownload:
    @staticmethod
    def check_data(folder, job_raster):
        assert folder.exists()
        name = folder.name

        tif = folder / f"{name}.tif"
        assert tif.exists()
        assert job_raster.exists()
        assert tif != job_raster
        assert Raster(tif) == Raster(job_raster)

        xml = folder / f"{name}.xml"
        assert xml.exists()
        assert xml.read_text() == "An XML metadata file in the job"

    @patch("pfdf.data.landfire._validate.refresh_rate")
    @patch("requests.get")
    def test_default_path(
        self, get_mock, refresh_mock, download_mock, job_raster, tmp_path, monkeypatch
    ):
        get_mock.side_effect = download_mock
        refresh_mock.return_value = 0.1
        monkeypatch.chdir(tmp_path)

        path = tmp_path / "landfire-240EVT"
        assert not path.exists()

        output = _landfire.download(
            "240EVT", [-107.8, 32.2, -107.6, 32.4, 4326], "test@usgs.gov"
        )
        assert output == path
        assert path.exists()
        self.check_data(path, job_raster)

    @patch("pfdf.data.landfire._validate.refresh_rate")
    @patch("requests.get")
    def test_custom_path(
        self, get_mock, refresh_mock, download_mock, job_raster, tmp_path
    ):
        get_mock.side_effect = download_mock
        refresh_mock.return_value = 0.1

        parent = tmp_path
        name = "test"
        path = parent / name
        assert not path.exists()

        output = _landfire.download(
            "240EVT",
            [-107.8, 32.2, -107.6, 32.4, 4326],
            "test@usgs.gov",
            parent=parent,
            name=name,
        )

        assert output == path
        assert path.exists()
        self.check_data(path, job_raster)

    @patch("pfdf.data.landfire._validate.max_job_time")
    @patch("pfdf.data.landfire._validate.refresh_rate")
    @patch("requests.get")
    def test_timeout(
        self, get_mock, refresh_mock, max_mock, timeout_mock, tmp_path, assert_contains
    ):

        get_mock.side_effect = timeout_mock
        refresh_mock.return_value = 0.1
        max_mock.return_value = 0.3

        parent = tmp_path
        name = "test"
        path = parent / name
        assert not path.exists()

        with pytest.raises(LFPSJobTimeoutError) as error:
            _landfire.download(
                "240EVT",
                [-107.8, 32.2, -107.6, 32.4, 4326],
                "test@usgs.gov",
                parent=parent,
                name=name,
            )
        assert_contains(error, "LANDFIRE LFPS took too long to process job 12345")
        assert not path.exists()


class TestRead:
    @patch("pfdf.data.landfire._validate.refresh_rate")
    @patch("requests.get")
    def test(_, get_mock, refresh_mock, download_mock, job_raster):
        get_mock.side_effect = download_mock
        refresh_mock.return_value = 0.1

        output = _landfire.read(
            "240EVT", [-107.8, 32.2, -107.6, 32.4, 4326], "test@usgs.gov"
        )
        assert isinstance(output, Raster)
        assert output == Raster(job_raster)

    @patch("pfdf.data.landfire._validate.refresh_rate")
    @patch("requests.get")
    def test_not_raster(_, get_mock, refresh_mock, vector_mock, assert_contains):
        get_mock.side_effect = vector_mock
        refresh_mock.return_value = 0.1

        with pytest.raises(FileNotFoundError) as error:
            _landfire.read(
                "test-layer", [-107.8, 32.2, -107.6, 32.4, 4326], "test@usgs.gov"
            )
        assert_contains(
            error, "Could not locate a raster dataset for the layer (test-layer)"
        )


@pytest.mark.web
class TestLive:
    def test(_):
        output = _landfire.read(
            "240EVT", [-107.8, 32.2, -107.6, 32.4, 4326], "pfdf@usgs.gov"
        )
        assert isinstance(output, Raster)
        assert output.shape == (740, 629)
        assert output.dtype == "int16"
        assert output.nodata == -9999
        assert output.crs.name == "North_American_1983_Albers"

        output = output.transform.remove_crs()
        expected = Transform(30, -30, -9435, 11115.0)
        assert output.isclose(expected)
