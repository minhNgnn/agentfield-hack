"""
Unit tests for mock_patients.json data

Tests validate:
1. JSON structure is valid
2. All required fields are present
3. Data types are correct
4. Each patient has the expected risk profile for demo
"""

import pytest
import json
from pathlib import Path


@pytest.fixture
def mock_patients():
    """Load mock patients data."""
    data_path = Path(__file__).parent.parent / "data" / "mock_patients.json"
    with open(data_path) as f:
        return json.load(f)


class TestMockPatientsStructure:
    """Tests for mock patients data structure."""

    def test_is_list(self, mock_patients):
        """Test that data is a list."""
        assert isinstance(mock_patients, list)

    def test_has_three_patients(self, mock_patients):
        """Test that we have exactly 3 demo patients."""
        assert len(mock_patients) == 3

    def test_patient_ids_unique(self, mock_patients):
        """Test that all patient IDs are unique."""
        patient_ids = [p["patient_id"] for p in mock_patients]
        assert len(patient_ids) == len(set(patient_ids))

    def test_expected_patient_ids(self, mock_patients):
        """Test that expected patient IDs exist."""
        patient_ids = {p["patient_id"] for p in mock_patients}
        assert patient_ids == {"P001", "P002", "P003"}


class TestPatientRequiredFields:
    """Tests for required fields in each patient."""

    REQUIRED_FIELDS = ["patient_id", "name", "age", "conditions", "medications", "labs", "vitals"]

    def test_all_required_fields_present(self, mock_patients):
        """Test that all required fields are present in each patient."""
        for patient in mock_patients:
            for field in self.REQUIRED_FIELDS:
                assert field in patient, f"Patient {patient.get('patient_id', 'unknown')} missing field: {field}"

    def test_age_is_positive_integer(self, mock_patients):
        """Test that age is a positive integer."""
        for patient in mock_patients:
            assert isinstance(patient["age"], int)
            assert patient["age"] > 0
            assert patient["age"] < 150

    def test_conditions_is_list(self, mock_patients):
        """Test that conditions is a list of strings."""
        for patient in mock_patients:
            assert isinstance(patient["conditions"], list)
            for condition in patient["conditions"]:
                assert isinstance(condition, str)

    def test_medications_is_list(self, mock_patients):
        """Test that medications is a list of strings."""
        for patient in mock_patients:
            assert isinstance(patient["medications"], list)
            for medication in patient["medications"]:
                assert isinstance(medication, str)


class TestLabsStructure:
    """Tests for labs data structure."""

    def test_labs_is_dict(self, mock_patients):
        """Test that labs is a dictionary."""
        for patient in mock_patients:
            assert isinstance(patient["labs"], dict)

    def test_labs_have_values_and_dates(self, mock_patients):
        """Test that each lab has values and dates arrays."""
        for patient in mock_patients:
            for lab_name, lab_data in patient["labs"].items():
                assert "values" in lab_data, f"Lab {lab_name} missing 'values'"
                assert "dates" in lab_data, f"Lab {lab_name} missing 'dates'"
                assert isinstance(lab_data["values"], list)
                assert isinstance(lab_data["dates"], list)

    def test_labs_values_and_dates_same_length(self, mock_patients):
        """Test that values and dates arrays have same length."""
        for patient in mock_patients:
            for lab_name, lab_data in patient["labs"].items():
                assert len(lab_data["values"]) == len(lab_data["dates"]), \
                    f"Lab {lab_name} has mismatched values/dates length"

    def test_labs_have_at_least_2_values(self, mock_patients):
        """Test that labs have at least 2 values for trend analysis."""
        for patient in mock_patients:
            for lab_name, lab_data in patient["labs"].items():
                assert len(lab_data["values"]) >= 2, \
                    f"Lab {lab_name} needs at least 2 values for trend analysis"

    def test_labs_values_are_numeric(self, mock_patients):
        """Test that lab values are numeric."""
        for patient in mock_patients:
            for lab_name, lab_data in patient["labs"].items():
                for value in lab_data["values"]:
                    assert isinstance(value, (int, float)), \
                        f"Lab {lab_name} has non-numeric value: {value}"


class TestVitalsStructure:
    """Tests for vitals data structure."""

    def test_vitals_is_dict(self, mock_patients):
        """Test that vitals is a dictionary."""
        for patient in mock_patients:
            assert isinstance(patient["vitals"], dict)

    def test_vitals_have_values_and_dates(self, mock_patients):
        """Test that each vital has values and dates arrays."""
        for patient in mock_patients:
            for vital_name, vital_data in patient["vitals"].items():
                assert "values" in vital_data, f"Vital {vital_name} missing 'values'"
                assert "dates" in vital_data, f"Vital {vital_name} missing 'dates'"

    def test_vitals_values_and_dates_same_length(self, mock_patients):
        """Test that values and dates arrays have same length."""
        for patient in mock_patients:
            for vital_name, vital_data in patient["vitals"].items():
                assert len(vital_data["values"]) == len(vital_data["dates"]), \
                    f"Vital {vital_name} has mismatched values/dates length"

    def test_heart_rate_present(self, mock_patients):
        """Test that heart_rate vital is present for all patients."""
        for patient in mock_patients:
            assert "heart_rate" in patient["vitals"], \
                f"Patient {patient['patient_id']} missing heart_rate vital"


class TestDemoScenarios:
    """Tests for demo scenario correctness."""

    def test_p001_high_risk_profile(self, mock_patients):
        """Test P001 has high-risk characteristics."""
        p001 = next(p for p in mock_patients if p["patient_id"] == "P001")
        
        # Age > 60
        assert p001["age"] >= 60
        
        # Has multiple conditions
        assert len(p001["conditions"]) >= 2
        
        # CRP is elevated and rising
        crp_values = p001["labs"]["CRP"]["values"]
        assert crp_values[-1] > 10  # Elevated
        assert crp_values[-1] > crp_values[0]  # Rising
        
        # Heart rate is increasing
        hr_values = p001["vitals"]["heart_rate"]["values"]
        assert hr_values[-1] > hr_values[0]

    def test_p002_low_risk_profile(self, mock_patients):
        """Test P002 has low-risk characteristics."""
        p002 = next(p for p in mock_patients if p["patient_id"] == "P002")
        
        # Younger age
        assert p002["age"] < 50
        
        # Few/minor conditions
        assert len(p002["conditions"]) <= 1
        
        # CRP is normal and stable
        crp_values = p002["labs"]["CRP"]["values"]
        assert all(v < 5 for v in crp_values)  # All normal
        
        # Heart rate is stable (within 10% variance)
        hr_values = p002["vitals"]["heart_rate"]["values"]
        avg_hr = sum(hr_values) / len(hr_values)
        assert all(abs(v - avg_hr) / avg_hr < 0.1 for v in hr_values)

    def test_p003_ambiguous_profile(self, mock_patients):
        """Test P003 has ambiguous characteristics."""
        p003 = next(p for p in mock_patients if p["patient_id"] == "P003")
        
        # Middle age
        assert 40 <= p003["age"] <= 60
        
        # CRP rising but still in range
        crp_values = p003["labs"]["CRP"]["values"]
        assert crp_values[-1] > crp_values[0]  # Rising
        assert crp_values[-1] <= 10  # Still within normal range


class TestDataConsistency:
    """Tests for overall data consistency."""

    def test_all_dates_valid_format(self, mock_patients):
        """Test that all dates are in YYYY-MM-DD format."""
        import re
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        
        for patient in mock_patients:
            for lab_data in patient["labs"].values():
                for date in lab_data["dates"]:
                    assert date_pattern.match(date), f"Invalid date format: {date}"
            
            for vital_data in patient["vitals"].values():
                for date in vital_data["dates"]:
                    assert date_pattern.match(date), f"Invalid date format: {date}"

    def test_dates_are_chronological(self, mock_patients):
        """Test that dates are in chronological order."""
        for patient in mock_patients:
            for lab_data in patient["labs"].values():
                dates = lab_data["dates"]
                assert dates == sorted(dates), "Lab dates not in chronological order"
            
            for vital_data in patient["vitals"].values():
                dates = vital_data["dates"]
                assert dates == sorted(dates), "Vital dates not in chronological order"
