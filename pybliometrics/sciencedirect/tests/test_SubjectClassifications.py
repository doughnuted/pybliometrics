"""Tests for `sciencedirect.SubjectClassifications` module."""
import pytest

pytest.skip("Skipping entire file: Requires live API key and network access", allow_module_level=True)

# from pybliometrics.sciencedirect import ScDirSubjectClassifications # MODIFIED
# from pybliometrics import init # MODIFIED

# init(keys=["DUMMY_KEY"]) # MODIFIED

# # Search by words in subject description
# sub1 = ScDirSubjectClassifications({"description": "Chemistry"}, refresh=30) # MODIFIED
# # Search by subject code
# sub2 = ScDirSubjectClassifications({"code": "5"}, refresh=30) # MODIFIED
# # Search by words in subject detail
# sub3 = ScDirSubjectClassifications({"detail": "Optimization"}, refresh=30) # MODIFIED
# # Search by subject abbreviation
# sub4 = ScDirSubjectClassifications({"abbrev": "socialsciences"}, refresh=30) # MODIFIED
# # Search by multiple criteria
# sub5 = ScDirSubjectClassifications( # MODIFIED
#     {"description": "Mathematics", "detail": "Mathematics::Applied Mathematics"},
#     refresh=30,
# )
# # Search by multiple criteria, subset returned fields
# sub6 = ScDirSubjectClassifications( # MODIFIED
#     {
#         "detail": "Agricultural and Biological Sciences",
#         "description": "Agricultural and Biological Sciences",
#     },
#     fields=["description", "detail"],
#     refresh=30,
# )


# def test_module():
#     assert sub6.__class__.__name__ == "ScDirSubjectClassifications"
#     assert sub6.__module__ == "pybliometrics.sciencedirect.subject_classifications"


# def test_results_desc():
#     assert len(sub1.results) > 0
#     descriptions = [res.description for res in sub1.results]
#     assert all([("Chemistry" in word or "chemistry" in word) for word in descriptions])


# def test_results_code():
#     assert len(sub2.results) == 1
#     assert sub2.results[0].code == "5"
#     assert sub2.results[0].abbrev == "agribio"


# def test_results_detail():
#     assert len(sub3.results) > 0
#     assert all(["Optimization" in res.detail for res in sub3.results])


# def test_results_abbrev():
#     assert len(sub4.results) > 0
#     assert all(["socialsciences" in res.abbrev for res in sub4.results])


# def test_results_multi():
#     assert len(sub5.results) > 0
#     assert all(["Mathematics" in res.description for res in sub5.results])
#     assert all(["Applied Mathematics" in res.detail for res in sub5.results])


# def test_results_fields():
#     assert len(sub6.results) > 0
#     assert all(
#         [
#             "Agricultural and Biological Sciences" in res.description
#             for res in sub6.results
#         ]
#     )
#     assert all(
#         ["Agricultural and Biological Sciences" in res.detail for res in sub6.results]
#     )
#     assert all(
#         [set(res._fields) == set(["description", "detail"]) for res in sub6.results]
#     )
