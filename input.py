import streamlit as st
import pandas as pd
import numpy as np
import io
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# Kelas untuk menangani data analisis gait
class GaitAnalysisData:
    def __init__(self, content, usia, jenis_kelamin):
        try:
            # Membaca file Excel ke dalam DataFrame pandas
            self.df = pd.read_excel(io.BytesIO(content), sheet_name=[0, 1])
            self.suin = self.df[0]  # Lembar pertama untuk data mentah
            self.normkin = self.df[1].iloc[:, :31]  # Lembar kedua untuk kinematika terstandarisasi           
        except Exception as e:
            st.error(f"Error membaca file Excel: {e}")
            return

        try:
            # Memproses data
            self.cleaned_data = self.clean_data()
            self.normkin_processed = self.process_normkin()
            self.trial_info = self.extract_trial_info()
            self.subject_params = self.extract_subject_params(usia, jenis_kelamin)
            self.body_measurements = self.extract_body_measurements()
            self.norm_kinematics = self.extract_norm_kinematics()
        except Exception as e:
            st.error(f"Terjadi kesalahan saat memproses data: {e}")

    def clean_data(self):
        cleaned_data = self.suin.dropna(how='all')
        cleaned_data.reset_index(drop=True, inplace=True)
        return cleaned_data

    def process_normkin(self):
        column_namesX = [col for col in self.normkin.columns if col.endswith('X')]
        normkin = self.normkin.loc[:, column_namesX]
        normkin.insert(0, "Percentage of Gait Cycle", self.df[1].iloc[:, 0].tolist())

        # Validasi data normkin
        for col in normkin.columns[1:]:  # Lewati kolom 'Percentage of Gait Cycle'
            if normkin[col].isnull().any():
                raise ValueError(f"Kolom '{col}' memiliki nilai NaN.")
            if (normkin[col] == 0).all():
                raise ValueError(f"Kolom '{col}' seluruhnya bernilai 0.")
            if not pd.api.types.is_numeric_dtype(normkin[col]):
                raise ValueError(f"Kolom '{col}' mengandung data non-numerik.")

        return normkin

    def extract_trial_info(self):
        return {
            "Trial Information": {
                "Trial Name": self.cleaned_data.iloc[1, 2]
            }
        }

    def extract_subject_params(self, usia, jenis_kelamin):
        bmi = (self.cleaned_data.iloc[4, 2])/((self.cleaned_data.iloc[5, 2]/1000)**2)
        bmi_class = (
            "Kurus Berat" if bmi < 17.0 else
            "Kurus Ringan" if 17.0 <= bmi <= 18.4 else
            "Normal" if 18.5 <= bmi <= 25.0 else
            "Gemuk Ringan" if 25.1 <= bmi <= 27.0 else
            "Gemuk Berat"
        )
        return {
            "Subject Parameters": {
                "Subject Name": self.cleaned_data.iloc[3, 2],
                "Age": usia,
                "Gender": jenis_kelamin.upper(),
                "Bodymass (kg)": self.cleaned_data.iloc[4, 2],
                "Height (mm)": self.cleaned_data.iloc[5, 2],
                "BMI": bmi,
                "BMI Classification": bmi_class
            }
        }

    def extract_body_measurements(self):
        return {
            "Body Measurements": {
                "Leg Length (mm)": {
                    "Left": self.cleaned_data.iloc[12, 2],
                    "Right": self.cleaned_data.iloc[12, 3]
                },
                "Knee Width (mm)": {
                    "Left": self.cleaned_data.iloc[13, 2],
                    "Right": self.cleaned_data.iloc[13, 3]
                },
                "Ankle Width (mm)": {
                    "Left": self.cleaned_data.iloc[14, 2],
                    "Right": self.cleaned_data.iloc[14, 3]
                }
            }
        }

    def extract_norm_kinematics(self):
        return {
            "Norm Kinematics": {
                "Percentage of Gait Cycle": self.normkin_processed['Percentage of Gait Cycle'].tolist(),
                "LPelvisAngles_X": self.normkin_processed["LPelvisAngles_X"].tolist(),
                "RPelvisAngles_X": self.normkin_processed["RPelvisAngles_X"].tolist(),
                "LHipAngles_X": self.normkin_processed["LHipAngles_X"].tolist(),
                "RHipAngles_X": self.normkin_processed["RHipAngles_X"].tolist(),
                "LKneeAngles_X": self.normkin_processed["LKneeAngles_X"].tolist(),
                "RKneeAngles_X": self.normkin_processed["RKneeAngles_X"].tolist(),
                "LAnkleAngles_X": self.normkin_processed["LAnkleAngles_X"].tolist(),
                "RAnkleAngles_X": self.normkin_processed["RAnkleAngles_X"].tolist(),
                "LFootProgressAngles_X": self.normkin_processed["LFootProgressAngles_X"].tolist(),
                "RFootProgressAngles_X": self.normkin_processed["RFootProgressAngles_X"].tolist()
            }
        }

    def to_dict(self):
        return {
            **self.trial_info,
            **self.subject_params,
            **self.body_measurements,
            **self.norm_kinematics
        }

# Streamlit UI
st.title("Gait Analysis Data Upload")
uploaded_file = st.file_uploader("Upload Excel File", type="xlsx")

if uploaded_file is not None:
    usia = st.number_input("Enter Age:", min_value=0, max_value=120)
    jenis_kelamin = st.text_input("Enter Gender (L/P):").strip().upper()

    if st.button("Process File"):
        content = uploaded_file.read()
        try:
            gait_data = GaitAnalysisData(content, usia, jenis_kelamin)
        except Exception as e:
            st.error(f"Gagal memproses file: {e}")
            gait_data = None

        if gait_data and hasattr(gait_data, 'df'):
            data_dict = gait_data.to_dict()

            # Create a new client and connect to the server
            client = MongoClient(st.secrets["MONGO_URI"])            
            db = client['GaitDB']
            collection = db['gait_data']

            try:
                collection.insert_one(data_dict)
                st.success("Data berhasil disimpan ke MongoDB!")
            except Exception as e:
                st.error(f"Gagal menyimpan data ke MongoDB: {e}")
        else:
            st.warning("File tidak valid atau gagal diproses.")
