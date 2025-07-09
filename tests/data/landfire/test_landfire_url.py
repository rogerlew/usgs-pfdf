import pytest

from pfdf.data.landfire import url

#####
# Base
#####


class TestApi:
    def test(_):
        assert url.api() == "https://lfps.usgs.gov/api"


class TestQuery:
    def test(_):
        output = url._query("test")
        assert output == "https://lfps.usgs.gov/api/test"


class TestProducts:
    def test(_):
        assert url.products() == "https://lfps.usgs.gov/api/products"


class TestJob:
    def test_base(_):
        assert url.job() == "https://lfps.usgs.gov/api/job"

    @pytest.mark.parametrize("action", ("cancel", "status", "submit"))
    def test_action(_, action):
        output = url.job(action)
        assert output == f"https://lfps.usgs.gov/api/job/{action}"

    def test_invalid_action(_, assert_contains):
        with pytest.raises(ValueError) as error:
            url.job("invalid")
        assert_contains(
            error,
            "action (invalid) is not a recognized option. Supported options are: cancel, status, submit",
        )


#####
# Job queries
#####


class TestSubmitJob:
    def test(_):
        output = url.submit_job(
            layers=["250EVT", "240EVT"],
            bounds=[-113.79, 42.29, -113.56, 42.148, 4326],
            email="test@usgs.gov",
        )
        assert (
            output
            == r"https://lfps.usgs.gov/api/job/submit?Layer_List=250EVT%3B240EVT&Area_of_Interest=-113.79+42.29+-113.56+42.148&Email=test%40usgs.gov"
        )

    def test_decode(_):
        output = url.submit_job(
            layers=["250EVT", "240EVT"],
            bounds=[-113.79, 42.29, -113.56, 42.148, 4326],
            email="test@usgs.gov",
            decode=True,
        )
        assert (
            output
            == r"https://lfps.usgs.gov/api/job/submit?Layer_List=250EVT;240EVT&Area_of_Interest=-113.79+42.29+-113.56+42.148&Email=test@usgs.gov"
        )

    def test_invalid(_, assert_contains):
        with pytest.raises(TypeError) as error:
            url.submit_job(
                layers=["250EVT", "240EVT"],
                bounds=[-113.79, 42.29, -113.56, 42.148, 4326],
                email=5,
            )
        assert_contains(error, "email must be a string")


class TestJobStatus:
    def test(_):
        output = url.job_status("abc123()")
        assert output == r"https://lfps.usgs.gov/api/job/status?JobId=abc123%28%29"

    def test_decode(_):
        output = url.job_status("abc123()", decode=True)
        assert output == r"https://lfps.usgs.gov/api/job/status?JobId=abc123()"

    def test_invalid(_, assert_contains):
        with pytest.raises(TypeError) as error:
            url.job_status(123)
        assert_contains(error, "job id must be a string")
