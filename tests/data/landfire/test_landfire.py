from unittest.mock import patch

import numpy as np
import pytest

from pfdf.data.landfire import _landfire
from pfdf.errors import DataAPIError, InvalidLFPSJobError, LFPSJobTimeoutError
from pfdf.projection import Transform
from pfdf.raster import Raster


@pytest.fixture
def completed_job():
    return {
        "jobId": "12345",
        "jobStatus": "esriJobSucceeded",
        "results": {
            "Output_File": {
                "paramUrl": "results/Output_File",
            }
        },
    }


@pytest.fixture
def results(download_url):
    return {
        "paramName": "Output_File",
        "dataType": "GPDataFile",
        "value": {
            "url": download_url,
        },
    }


@pytest.fixture
def download_url():
    return "https://lfps.usgs.gov/arcgis/rest/directories/arcgisjobs/landfireproductservice_gpserver/12345/scratch/12345.zip"


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
def download_mock(json_response, completed_job, results, zip_data):
    "Returns a function that mocks requests.get for downloading files"

    def download_mock(url, *args, **kwargs):
        "Mocks requests.get for downloading files"

        # Job submission
        if (
            url
            == "https://lfps.usgs.gov/arcgis/rest/services/LandfireProductService/GPServer/LandfireProductService/submitJob"
        ):
            return json_response({"jobId": "12345", "jobStatus": "esriJobSubmitted"})

        # Job completion
        elif (
            url
            == "https://lfps.usgs.gov/arcgis/rest/services/LandfireProductService/GPServer/LandfireProductService/jobs/12345"
        ):
            return json_response(completed_job)

        # Job results
        elif (
            url
            == "https://lfps.usgs.gov/arcgis/rest/services/LandfireProductService/GPServer/LandfireProductService/jobs/12345/results/Output_File"
        ):
            return json_response(results)

        # File download
        elif (
            url
            == "https://lfps.usgs.gov/arcgis/rest/directories/arcgisjobs/landfireproductservice_gpserver/12345/scratch/12345.zip"
        ):
            return zip_data

    return download_mock


@pytest.fixture
def timeout_mock(json_response):
    "Returns a function used to mock requests.get for timed out jobs"

    def timeout_mock(url, *args, **kwargs):

        # Job submission
        if (
            url
            == "https://lfps.usgs.gov/arcgis/rest/services/LandfireProductService/GPServer/LandfireProductService/submitJob"
        ):
            return json_response({"jobId": "12345", "jobStatus": "esriJobSubmitted"})

        # Job never finishes
        elif (
            url
            == "https://lfps.usgs.gov/arcgis/rest/services/LandfireProductService/GPServer/LandfireProductService/jobs/12345"
        ):
            return json_response({"jobId": "12345", "jobStatus": "esriJobExecuting"})

    return timeout_mock


@pytest.fixture
def vector_mock(json_response, completed_job, results, zip_vector):
    "Returns a function that mocks requests.get for downloading files"

    def vector_mock(url, *args, **kwargs):
        "Mocks requests.get for downloading vector files"

        # Job submission
        if (
            url
            == "https://lfps.usgs.gov/arcgis/rest/services/LandfireProductService/GPServer/LandfireProductService/submitJob"
        ):
            return json_response({"jobId": "12345", "jobStatus": "esriJobSubmitted"})

        # Job completion
        elif (
            url
            == "https://lfps.usgs.gov/arcgis/rest/services/LandfireProductService/GPServer/LandfireProductService/jobs/12345"
        ):
            return json_response(completed_job)

        # Job results
        elif (
            url
            == "https://lfps.usgs.gov/arcgis/rest/services/LandfireProductService/GPServer/LandfireProductService/jobs/12345/results/Output_File"
        ):
            return json_response(results)

        # File download
        elif (
            url
            == "https://lfps.usgs.gov/arcgis/rest/directories/arcgisjobs/landfireproductservice_gpserver/12345/scratch/12345.zip"
        ):
            return zip_vector

    return vector_mock


class TestCheckStatus:
    @pytest.mark.parametrize("status", ("New", "Executing", "Submitted", "Waiting"))
    def test_running(_, status):
        job = {"jobId": "12345", "jobStatus": f"esriJob{status}"}
        assert _landfire._check_status(job) == False

    def test_succeeded(_):
        job = {"jobId": "12345", "jobStatus": "esriJobSucceeded"}
        assert _landfire._check_status(job) == True

    @pytest.mark.parametrize("status", ("Cancelling", "Cancelled"))
    def test_cancelled(_, status, assert_contains):
        job = {"jobId": "12345", "jobStatus": f"esriJob{status}"}
        with pytest.raises(InvalidLFPSJobError) as error:
            _landfire._check_status(job)
        assert_contains(
            error, "Cannot download job 12345 because the job was cancelled"
        )

    def test_timed_out(_, assert_contains):
        job = {"jobId": "12345", "jobStatus": f"esriJobTimedOut"}
        with pytest.raises(LFPSJobTimeoutError) as error:
            _landfire._check_status(job)
        assert_contains(error, "Cannot download job 12345 because the job timed out")

    @pytest.mark.parametrize("status", ("esriJobFailed", "expectedFailure"))
    def test_failed(_, status, assert_contains):
        job = {"jobId": "12345", "jobStatus": status}
        with pytest.raises(InvalidLFPSJobError) as error:
            _landfire._check_status(job)
        assert_contains(error, "Cannot download job 12345 because the job failed")

    def test_unrecognized(_, assert_contains):
        job = {"jobId": "12345", "jobStatus": "UnrecognizedStatus"}
        with pytest.raises(DataAPIError) as error:
            _landfire._check_status(job)
        assert_contains(
            error,
            "LANDFIRE LFPS returned an unrecognized status code: UnrecognizedStatus",
        )


class TestExecuteJob:
    @patch("requests.get")
    def test_success(_, mock, json_response):
        running = {"jobId": "12345", "jobStatus": "esriJobExecuting"}
        finished = {"jobId": "12345", "jobStatus": "esriJobSucceeded"}
        responses = [json_response(status) for status in [running] * 3 + [finished]]
        mock.side_effect = responses

        output = _landfire._execute_job("12345", 15, 0.1, None)
        assert output == finished
        mock.assert_called_with(
            "https://lfps.usgs.gov/arcgis/rest/services/LandfireProductService/GPServer/LandfireProductService/jobs/12345",
            params={"f": "json"},
            timeout=None,
        )

    @patch("requests.get")
    def test_failed(_, mock, json_response, assert_contains):
        running = {"jobId": "12345", "jobStatus": "esriJobExecuting"}
        failed = {"jobId": "12345", "jobStatus": "esriJobFailed"}
        responses = [json_response(status) for status in [running] * 3 + [failed]]
        mock.side_effect = responses

        with pytest.raises(InvalidLFPSJobError) as error:
            _landfire._execute_job("12345", 15, 0.1, None)
        assert_contains(error, "Cannot download job 12345 because the job failed")
        mock.assert_called_with(
            "https://lfps.usgs.gov/arcgis/rest/services/LandfireProductService/GPServer/LandfireProductService/jobs/12345",
            params={"f": "json"},
            timeout=None,
        )

    @patch("requests.get")
    def test_timed_out(_, mock, json_response, assert_contains):
        running = {"jobId": "12345", "jobStatus": "esriJobExecuting"}
        responses = [json_response(running)] * 5
        mock.side_effect = responses

        with pytest.raises(LFPSJobTimeoutError) as error:
            _landfire._execute_job(
                "12345", max_job_time=0.4, refresh_rate=0.1, timeout=None
            )
        assert_contains(error, "LANDFIRE LFPS took too long to process job 12345")
        mock.assert_called_with(
            "https://lfps.usgs.gov/arcgis/rest/services/LandfireProductService/GPServer/LandfireProductService/jobs/12345",
            params={"f": "json"},
            timeout=None,
        )


class TestParseUrl:
    @patch("requests.get")
    def test(_, mock, json_response, completed_job, results, download_url):
        mock.return_value = json_response(results)
        output = _landfire._parse_url(completed_job, "12345", None)
        assert output == download_url
        mock.assert_called_with(
            "https://lfps.usgs.gov/arcgis/rest/services/LandfireProductService/GPServer/LandfireProductService/jobs/12345/results/Output_File",
            params={"f": "json"},
            timeout=None,
        )


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

        output = _landfire.download("240EVT", [-107.8, 32.2, -107.6, 32.4, 4326])
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
            "240EVT", [-107.8, 32.2, -107.6, 32.4, 4326], parent=parent, name=name
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
                "240EVT", [-107.8, 32.2, -107.6, 32.4, 4326], parent=parent, name=name
            )
        assert_contains(error, "LANDFIRE LFPS took too long to process job 12345")
        assert not path.exists()


class TestRead:
    @patch("pfdf.data.landfire._validate.refresh_rate")
    @patch("requests.get")
    def test(_, get_mock, refresh_mock, download_mock, job_raster):
        get_mock.side_effect = download_mock
        refresh_mock.return_value = 0.1

        output = _landfire.read("240EVT", [-107.8, 32.2, -107.6, 32.4, 4326])
        assert isinstance(output, Raster)
        assert output == Raster(job_raster)

    @patch("pfdf.data.landfire._validate.refresh_rate")
    @patch("requests.get")
    def test_not_raster(_, get_mock, refresh_mock, vector_mock, assert_contains):
        get_mock.side_effect = vector_mock
        refresh_mock.return_value = 0.1

        with pytest.raises(FileNotFoundError) as error:
            _landfire.read("test-layer", [-107.8, 32.2, -107.6, 32.4, 4326])
        assert_contains(
            error, "Could not locate a raster dataset for the layer (test-layer)"
        )


@pytest.mark.web
class TestLive:
    def test(_):
        output = _landfire.read("240EVT", [-107.8, 32.2, -107.6, 32.4, 4326])
        assert isinstance(output, Raster)
        assert output.shape == (740, 629)
        assert output.dtype == "int16"
        assert output.nodata == -9999
        assert output.crs.name == "North_American_1983_Albers"

        output = output.transform.remove_crs()
        expected = Transform(30, -30, -9435, 11115.0)
        assert output.isclose(expected)
