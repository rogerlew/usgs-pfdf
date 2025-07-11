from unittest.mock import patch

import pytest

from pfdf.data.landfire import job
from pfdf.errors import DataAPIError, MissingAPIFieldError, MissingCRSError


def check_status_mock(mock):
    mock.assert_called_with(
        url="https://lfps.usgs.gov/api/job/status",
        params={"JobId": "12345"},
        timeout=10,
    )


@pytest.fixture
def missing():
    return {"success": False, "message": "JobId not found"}


@pytest.fixture
def missing_job(missing, json_response):
    return json_response(missing)


class TestSubmit:
    @patch("requests.get", spec=True)
    def test(_, mock, json_response):
        content = {
            "jobId": "12345",
        }
        mock.return_value = json_response(content)

        layers = ["240EVT", "230EVT"]
        bounds = [-107.6, 32.2, -107.2, 32.8, 4326]
        output = job.submit(layers, bounds, "test@usgs.gov")
        assert output == "12345"
        mock.assert_called_with(
            url="https://lfps.usgs.gov/api/job/submit",
            params={
                "Layer_List": "240EVT;230EVT",
                "Area_of_Interest": "-107.6 32.2 -107.2 32.8",
                "Email": "test@usgs.gov",
            },
            timeout=10,
        )

    def test_no_crs(_, assert_contains):
        layers = "240EVT"
        bounds = [-107.6, 32.2, -107.2, 32.8]
        with pytest.raises(MissingCRSError) as error:
            job.submit(layers, bounds, "test@usgs.gov")
        assert_contains(error, "bounds must have a CRS")


class TestStatus:
    @patch("requests.get", spec=True)
    def test(_, mock, json_response):
        content = {
            "jobId": "12345",
            "status": "Succeeded",
            "messages": ["Some", "messages"],
        }
        mock.return_value = json_response(content)
        output = job.status("12345")
        assert output == content
        check_status_mock(mock)

    @patch("requests.get", spec=True)
    def test_missing(_, mock, missing_job, assert_contains):
        mock.return_value = missing_job
        with pytest.raises(ValueError) as error:
            job.status("12345")
        assert_contains(
            error, "The queried job (12345) could not be found on the LFPS server"
        )
        check_status_mock(mock)

    @patch("requests.get", spec=True)
    def test_missing_not_strict(_, mock, missing_job, missing):
        mock.return_value = missing_job
        output = job.status("12345", strict=False)
        assert output == missing
        check_status_mock(mock)


class TestStatusCode:
    @patch("requests.get", spec=True)
    def test(_, mock, json_response):
        content = {"jobId": "12345", "status": "Succeeded"}
        mock.return_value = json_response(content)
        output = job.status_code("12345")
        assert output == "Succeeded"
        check_status_mock(mock)

    @patch("requests.get", spec=True)
    def test_missing(_, mock, missing_job, assert_contains):
        mock.return_value = missing_job
        with pytest.raises(ValueError) as error:
            job.status_code("12345")
        assert_contains(
            error, "The queried job (12345) could not be found on the LFPS server"
        )
        check_status_mock(mock)

    @patch("requests.get", spec=True)
    def test_no_status(_, mock, json_response, assert_contains):
        content = {"jobId": "12345"}
        mock.return_value = json_response(content)
        with pytest.raises(MissingAPIFieldError) as error:
            job.status_code("12345")
        assert_contains(error, "LANDFIRE LFPS failed to return the job status code")
        check_status_mock(mock)


class TestJobError:
    def test_missing_job(_):
        response = {"message": "JobId not found"}
        output = job._job_error(response, "12345")
        assert isinstance(output, ValueError)
        assert (
            "The queried job (12345) could not be found on the LFPS server"
            in output.args[0]
        )

    def test_other_error(_):
        response = {"message": "something failed"}
        output = job._job_error(response, "12345")
        assert isinstance(output, DataAPIError)
        assert (
            output.args[0]
            == "LANDFIRE LFPS reported the following error in the API query for job 12345:\nsomething failed"
        )

    def test_no_error_message(_):
        output = job._job_error({}, "12345")
        assert isinstance(output, DataAPIError)
        assert (
            output.args[0]
            == "LANDFIRE LFPS reported an error in the API query for job 12345"
        )
