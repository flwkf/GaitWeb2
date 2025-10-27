import pandas as pd
from pymongo import MongoClient
import math
import matplotlib.pyplot as plt
from PIL import Image
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from pymongo import MongoClient
import numpy as np
from pymongo.server_api import ServerApi

# Kelas GaitAnalysisData tetap sama seperti yang telah Anda buat sebelumnya
import pandas as pd
import numpy as np
st.set_page_config(layout="wide", initial_sidebar_state="expanded", page_title="Dashboard Gait Analysis")

class GaitAnalysisData:
    def __init__(self, data):
        self.df = pd.read_excel(data, sheet_name=[0, 1])  # Read the uploaded file
        self.suin = self.df[0]
        self.normkin = self.df[1].iloc[:, :31]

        # Clean and extract necessary data
        self.cleaned_data = self.clean_data()
        self.normkin_processed = self.process_normkin()

        # Extract and store various sections
        self.trial_info = self.extract_trial_info()
        self.subject_params = self.extract_subject_params()
        self.body_measurements = self.extract_body_measurements()
        self.norm_kinematics = self.extract_norm_kinematics()

    def clean_data(self):
        cleaned_data = self.suin.dropna(how='all')
        cleaned_data.reset_index(drop=True, inplace=True)
        return cleaned_data

    def process_normkin(self):
        column_namesX = [col for col in self.normkin.columns if col.endswith('X')]
        normkin = self.normkin.loc[:, column_namesX]
        normkin.insert(0, "Percentage of Gait Cycle", self.df[1].iloc[:, 0].tolist())
        return normkin

    def extract_trial_info(self):
        return {
            "Trial Information": {
                "Trial Name": self.cleaned_data.iloc[1, 2]
            }
        }

    def extract_subject_params(self):
        return {
            "Subject Parameters": {
                "Subject Name": self.cleaned_data.iloc[3, 2],
                "Bodymass (kg)": self.cleaned_data.iloc[4, 2],
                "Height (mm)": self.cleaned_data.iloc[5, 2]
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
                "Percentage of Gait Cycle": np.array(self.normkin_processed['Percentage of Gait Cycle'].values.tolist()),
                "LPelvisAngles_X": np.array(self.normkin_processed["LPelvisAngles_X"].values.tolist()),
                "RPelvisAngles_X": np.array(self.normkin_processed["RPelvisAngles_X"].values.tolist()),
                "LHipAngles_X": np.array(self.normkin_processed["LHipAngles_X"].values.tolist()),
                "RHipAngles_X": np.array(self.normkin_processed["RHipAngles_X"].values.tolist()),
                "LKneeAngles_X": np.array(self.normkin_processed["LKneeAngles_X"].values.tolist()),
                "RKneeAngles_X": np.array(self.normkin_processed["RKneeAngles_X"].values.tolist()),
                "LAnkleAngles_X": np.array(self.normkin_processed["LAnkleAngles_X"].values.tolist()),
                "RAnkleAngles_X": np.array(self.normkin_processed["RAnkleAngles_X"].values.tolist()),
                "LFootProgressAngles_X": np.array(self.normkin_processed["LFootProgressAngles_X"].values.tolist()),
                "RFootProgressAngles_X": np.array(self.normkin_processed["RFootProgressAngles_X"].values.tolist())
            }
        }

    def to_dict(self):
        # Combine all sections into a single dictionary
        return {
            **self.trial_info,
            **self.subject_params,
            **self.body_measurements,
            **self.norm_kinematics
        }

import replicate

def analyze_graph_with_llm(graph_type, mae_value, mean_diff, std_diff):
    """
    Mengirim prompt ke IBM Granite via Replicate untuk menghasilkan analisis teks.
    """
    prompt = f"""
    Kamu adalah analis medis yang menjelaskan hasil gait analysis.
    Grafik yang dianalisis: {graph_type}.
    Nilai MAE pasien: {mae_value:.2f} derajat.
    Rata-rata perbedaan sudut terhadap populasi normal: {mean_diff:.2f} derajat.
    Standar deviasi perbedaan: {std_diff:.2f} derajat.

    Jelaskan dengan bahasa sederhana apakah pola pergerakan sendi pasien ini
    masih dalam batas normal atau mengindikasikan kelainan pola jalan.
    Gunakan maksimal 4 kalimat dalam bahasa Indonesia.
    """

    try:
        output = replicate.run(
            "ibm-granite/granite-13b-chat:latest",
            input={
                "prompt": prompt,
                "temperature": 0.2,
                "max_new_tokens": 200
            },
            api_token=st.secrets["REPLICATE_API_TOKEN"]
        )
        return "".join(output)
    except Exception as e:
        return f"(Gagal mengambil analisis otomatis: {e})"

# Sidebar untuk upload file
uploaded_file = st.sidebar.file_uploader("upload patient data", type=["xlsx"])

if uploaded_file is not None:
    st.write("File uploaded:", uploaded_file.name)

    # Proses file dengan GaitAnalysisData
    try:
        # Inisialisasi objek
        gait_data = GaitAnalysisData(uploaded_file)

        # Ambil data hasil proses dalam bentuk dictionary
        processed_data = gait_data.to_dict()

        # Ekstraksi data untuk Norm Kinematics
        rows = []  # Untuk menyimpan baris data

        # Iterasi langsung ke Norm Kinematics
        norm_kinematics = processed_data["Norm Kinematics"]

        # Pastikan hanya satu iterasi untuk setiap elemen array
        for i in range(len(norm_kinematics["Percentage of Gait Cycle"])):  # Panjangnya 101
            row = {
                "%cycle": norm_kinematics["Percentage of Gait Cycle"][i],
                "LPelvisAngles_X": norm_kinematics["LPelvisAngles_X"][i],
                "RPelvisAngles_X": norm_kinematics["RPelvisAngles_X"][i],
                "LHipAngles_X": norm_kinematics["LHipAngles_X"][i],
                "RHipAngles_X": norm_kinematics["RHipAngles_X"][i],
                "LKneeAngles_X": norm_kinematics["LKneeAngles_X"][i],
                "RKneeAngles_X": norm_kinematics["RKneeAngles_X"][i],
                "LAnkleAngles_X": norm_kinematics["LAnkleAngles_X"][i],
                "RAnkleAngles_X": norm_kinematics["RAnkleAngles_X"][i],
            }
            rows.append(row)

        # Buat DataFrame
        norm_kinematics_df = pd.DataFrame(rows)

        # Tampilkan DataFrame
        # st.write("Norm Kinematics Data:")
        # st.dataframe(norm_kinematics_df)
        px.defaults.template = 'plotly_dark'
        px.defaults.color_continuous_scale = 'reds'
        # Koneksi ke MongoDB

        # Create a new client and connect to the server
        client = MongoClient(st.secrets["MONGO_URI"])
        # client = MongoClient('mongodb://localhost:27017/')
        db = client['GaitDB']
        collection = db['gait_data']
        
        # Membaca data dari MongoDB
        cursor = collection.find()  # Mengambil semua dokumen
        data = list(cursor)  # Mengonversi cursor menjadi list
        if len(data) == 0:
            st.error("The database does not have gait analysis data. Please add or upload the data first.")
            st.stop() 
        elif len(data) == 1:
            st.error("The database only has one gait analysis data. Please add or upload the data first.")
            st.stop() 
        # Normalisasi data untuk DataFrame
        df = pd.json_normalize(data)
        # Mengubah nama kolom untuk mempermudah akses
        df.columns = df.columns.str.replace('Trial Information.', '')
        df.columns = df.columns.str.replace('Subject Parameters.', '')
        df.columns = df.columns.str.replace('Body Measurements.', '')
        df.columns = df.columns.str.replace('Norm Kinematics.', '')

        st.title("Dashboard Gait Analysis")
        st.sidebar.title("Filter Data")
        # Filter usia
        min_age = df['Age'].min()
        max_age = df['Age'].max()
        age_range = st.sidebar.slider(
            'Filter by Age Range:',
            min_value=min_age,
            max_value=max_age,
            value=(min_age, max_age)  # Nilai default adalah keseluruhan rentang usia
        )

        # filter BMI
        bmi = ["All BMI Classification"] + list(df["BMI Classification"].value_counts().keys().sort_values())
        classbmi = st.sidebar.selectbox(label="BMI Classification", options=bmi)

        # filter gender
        gender_mapping = {
            "L": "Pria",
            "P": "Wanita"
        }
        df["Gender"] = df["Gender"].map(gender_mapping)
        gend = ["All Gender"] + list(df["Gender"].value_counts().keys().sort_values())
        gender = st.sidebar.selectbox(label="Gender", options=gend)

            
        filtered_df = df[(df['Age'] >= age_range[0]) & (df['Age'] <= age_range[1])]
        if classbmi != "All BMI Classification":
            filtered_df = filtered_df[filtered_df['BMI Classification'] == classbmi]
            if gender != "All Gender":
                filtered_df = filtered_df[filtered_df["Gender"] == gender]

        if gender != "All Gender":
            filtered_df = filtered_df[filtered_df["Gender"] == gender]
            
        if filtered_df.empty:
            st.error(f"Tidak terdapat data dengan jenis kelamin {gender} yang terklasifikasi {classbmi}")
        else:
            st.sidebar.markdown(f"**Total Records:** {len(filtered_df)}")
            # Pelvis
            percentage_cycle = pd.DataFrame(filtered_df['Percentage of Gait Cycle'].tolist())
            l_pelvis_angles = pd.DataFrame(filtered_df['LPelvisAngles_X'].tolist())
            r_pelvis_angles = pd.DataFrame(filtered_df['RPelvisAngles_X'].tolist())

            percentage_cycle.columns = [f"%cycle_{i}" for i in range(percentage_cycle.shape[1])]
            l_pelvis_angles.columns = [f"L_Pelvis_{i}" for i in range(l_pelvis_angles.shape[1])]
            r_pelvis_angles.columns = [f"R_Pelvis_{i}" for i in range(r_pelvis_angles.shape[1])]
            
            mean_l_pelvis = l_pelvis_angles.mean(axis=0).values
            std_l_pelvis = l_pelvis_angles.std(axis=0)/np.sqrt(l_pelvis_angles.shape[0])
            mean_r_pelvis = r_pelvis_angles.mean(axis=0).values
            std_r_pelvis = r_pelvis_angles.std(axis=0)/np.sqrt(r_pelvis_angles.shape[0])
 

            std_l_pelvis = std_l_pelvis.values if isinstance(std_l_pelvis, pd.Series) else std_l_pelvis
            std_r_pelvis = std_r_pelvis.values if isinstance(std_r_pelvis, pd.Series) else std_r_pelvis

            lpelvis = pd.DataFrame({
                "%cycle": list(range(101)),
                'Mean_Lpelvis': mean_l_pelvis,
                'std_Lpelvis': std_l_pelvis,
                'your left pelvis': norm_kinematics_df['LPelvisAngles_X']
            })

            rpelvis = pd.DataFrame({
                "%cycle": list(range(101)),
                'Mean_Rpelvis': mean_r_pelvis,
                'std_Rpelvis': std_r_pelvis,
                'your right pelvis': norm_kinematics_df['RPelvisAngles_X']
            })
            ## Create the figure
            fig1 = go.Figure()

            ## Add mean and shading for Left Pelvis
            fig1.add_trace(go.Scatter(
                x=lpelvis["%cycle"], 
                y=lpelvis["Mean_Lpelvis"], 
                mode='lines',
                name='Average Left Pelvis<br>(Normal Subjects)',
                line=dict(color='orange'),
                hoverinfo='text',
                text=[f"Average Normal Subjects: {cycle}%, {val:.2f}°" for cycle, val in zip(lpelvis["%cycle"], lpelvis["Mean_Lpelvis"])]
            ))
            fig1.add_trace(go.Scatter(
                x=lpelvis["%cycle"], 
                y=lpelvis["your left pelvis"], 
                mode='lines',
                name='Patient',
                line=dict(color='black')
            ))
            fig1.add_trace(go.Scatter(
                x=lpelvis["%cycle"], 
                y=lpelvis["Mean_Lpelvis"] + lpelvis["std_Lpelvis"], 
                mode='lines',
                name='Upper Bound (Left)',
                line=dict(color='orange', width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
            fig1.add_trace(go.Scatter(
                x=lpelvis["%cycle"], 
                y=lpelvis["Mean_Lpelvis"] - lpelvis["std_Lpelvis"], 
                mode='lines',
                name='Standard Error Area',
                line=dict(color='orange', width=0),
                fill='tonexty',  # Fill between this trace and the previous one
                fillcolor='rgba(255, 165, 0, 0.2)',
                showlegend=True,
                hoverinfo='text',
                text=[f"Upper Bound (Left): {cycle}%, {valup:.2f}°<br>Lower Bound (Left): {cycle}%, {vallow:.2f}°" for cycle, vallow, valup in zip(lpelvis["%cycle"], lpelvis["Mean_Lpelvis"] - lpelvis["std_Lpelvis"], lpelvis["Mean_Lpelvis"] + lpelvis["std_Lpelvis"])]
            ))
            
            ## Update layout
            fig1.update_layout(
                title="Left Pelvis",
                xaxis_title="%Cycle",
                yaxis_title="Value",
                template="plotly_dark",
                title_x=0.5,
                hovermode="x unified"
            )
            
            fig2 = go.Figure()
            ## Add mean and shading for Right Pelvis
            fig2.add_trace(go.Scatter(
                x=rpelvis["%cycle"], 
                y=rpelvis["Mean_Rpelvis"], 
                mode='lines',
                name='Average Right Pelvis<br>(Normal Subjects)',
                line=dict(color='dark blue'),
                hoverinfo='text',
                text=[f"Average Normal Subjects: {cycle}%, {val:.2f}°" for cycle, val in zip(rpelvis["%cycle"], rpelvis["Mean_Rpelvis"])]
            ))
            fig2.add_trace(go.Scatter(
                x=rpelvis["%cycle"], 
                y=rpelvis["your right pelvis"], 
                mode='lines',
                name='Patient',
                line=dict(color='black')
            ))
            fig2.add_trace(go.Scatter(
                x=rpelvis["%cycle"], 
                y=rpelvis["Mean_Rpelvis"] + rpelvis["std_Rpelvis"], 
                mode='lines',
                name='Upper Bound (Right)',
                line=dict(color='dark blue', width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
            fig2.add_trace(go.Scatter(
                x=rpelvis["%cycle"], 
                y=rpelvis["Mean_Rpelvis"] - rpelvis["std_Rpelvis"], 
                mode='lines',
                name='Standard Error Area',
                line=dict(color='dark blue', width=0),
                fill='tonexty',
                fillcolor='rgba(0, 255, 255, 0.2)',
                showlegend=True,
                hoverinfo='text',
                text=[f"Upper Bound (Right): {cycle}%, {valup:.2f}°<br>Lower Bound (Right): {cycle}%, {vallow:.2f}°" for cycle, vallow, valup in zip(rpelvis["%cycle"], rpelvis["Mean_Rpelvis"] - rpelvis["std_Rpelvis"], rpelvis["Mean_Rpelvis"] + rpelvis["std_Rpelvis"])]
    
            ))
            fig2.update_layout(
                title="Right Pelvis",
                xaxis_title="%Cycle",
                yaxis_title="Value",
                template="plotly_dark",
                title_x=0.5,
                hovermode="x unified"
            )

            # Knee
            percentage_cycle = pd.DataFrame(filtered_df['Percentage of Gait Cycle'].tolist())
            l_knee_angles = pd.DataFrame(filtered_df['LKneeAngles_X'].tolist())
            r_knee_angles = pd.DataFrame(filtered_df['RKneeAngles_X'].tolist())

            percentage_cycle.columns = [f"%cycle_{i}" for i in range(percentage_cycle.shape[1])]
            l_knee_angles.columns = [f"L_Knee_{i}" for i in range(l_knee_angles.shape[1])]
            r_knee_angles.columns = [f"R_Knee_{i}" for i in range(r_knee_angles.shape[1])]

            mean_l_knee = l_knee_angles.mean(axis=0).values
            std_l_knee = l_knee_angles.std(axis=0) / np.sqrt(l_knee_angles.shape[0])
            mean_r_knee = r_knee_angles.mean(axis=0).values
            std_r_knee = r_knee_angles.std(axis=0) / np.sqrt(r_knee_angles.shape[0])

            std_l_knee = std_l_knee.values if isinstance(std_l_knee, pd.Series) else std_l_knee
            std_r_knee = std_r_knee.values if isinstance(std_r_knee, pd.Series) else std_r_knee

            lknee = pd.DataFrame({
                "%cycle": list(range(101)),
                'Mean_Lknee': mean_l_knee,
                'std_Lknee': std_l_knee,
                'your left knee': norm_kinematics_df['LKneeAngles_X']
            })
            
            rknee = pd.DataFrame({
                "%cycle": list(range(101)),
                'Mean_Rknee': mean_r_knee,
                'std_Rknee': std_r_knee,
                'your right knee': norm_kinematics_df['RKneeAngles_X']
            })

            fig3 = go.Figure()

            fig3.add_trace(go.Scatter(
                x=lknee["%cycle"], 
                y=lknee["Mean_Lknee"], 
                mode='lines',
                name='Average Left Knee<br>(Normal Subjects)',
                line=dict(color='orange'),
                hoverinfo='text',
                text=[f"Average Normal Subjects: {cycle}%, {val:.2f}°" for cycle, val in zip(lknee["%cycle"], lknee["Mean_Lknee"])]
            ))
            fig3.add_trace(go.Scatter(
                x=lknee["%cycle"], 
                y=lknee["your left knee"], 
                mode='lines',
                name='Patient',
                line=dict(color='black')
            ))
            fig3.add_trace(go.Scatter(
                x=lknee["%cycle"], 
                y=lknee["Mean_Lknee"] + lknee["std_Lknee"], 
                mode='lines',
                name='Upper Bound (Left)',
                line=dict(color='orange', width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
            fig3.add_trace(go.Scatter(
                x=lknee["%cycle"], 
                y=lknee["Mean_Lknee"] - lknee["std_Lknee"], 
                mode='lines',
                name='Standard Error Area',
                line=dict(color='orange', width=0),
                fill='tonexty',
                fillcolor='rgba(255, 165, 0, 0.2)',
                showlegend=False,
                hoverinfo='text',
                text=[f"Upper Bound (Left): {cycle}%, {valup:.2f}°<br>Lower Bound (Left): {cycle}%, {vallow:.2f}°" for cycle, vallow, valup in zip(lknee["%cycle"], lknee["Mean_Lknee"] - lknee["std_Lknee"], lknee["Mean_Lknee"] + lknee["std_Lknee"])]
    
            ))
            
            fig3.update_layout(
                title="Left Knee",
                xaxis_title="%Cycle",
                yaxis_title="Value",
                template="plotly_dark",
                title_x=0.5,
                hovermode="x unified"
            )
            
            fig4 = go.Figure()
            fig4.add_trace(go.Scatter(
                x=rknee["%cycle"], 
                y=rknee["Mean_Rknee"], 
                mode='lines',
                name='Average Right Knee<br>(Normal Subjects)',
                line=dict(color='dark blue'),
                hoverinfo='text',
                text=[f"Average Normal Subjects: {cycle}%, {val:.2f}°" for cycle, val in zip(rknee["%cycle"], rknee["Mean_Rknee"])]
            ))
            fig4.add_trace(go.Scatter(
                x=rknee["%cycle"], 
                y=rknee["your right knee"], 
                mode='lines',
                name='Patient',
                line=dict(color='black')
            ))
            fig4.add_trace(go.Scatter(
                x=rknee["%cycle"], 
                y=rknee["Mean_Rknee"] + rknee["std_Rknee"], 
                mode='lines',
                name='Upper Bound (Right)',
                line=dict(color='dark blue', width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
            fig4.add_trace(go.Scatter(
                x=rknee["%cycle"], 
                y=rknee["Mean_Rknee"] - rknee["std_Rknee"], 
                mode='lines',
                name='Standard Error Area',
                line=dict(color='dark blue', width=0),
                fill='tonexty',
                fillcolor='rgba(0, 255, 255, 0.2)',
                showlegend=False,
                hoverinfo='text',
                text=[f"Upper Bound (Right): {cycle}%, {valup:.2f}°<br>Lower Bound (Right): {cycle}%, {vallow:.2f}°" for cycle, vallow, valup in zip(rknee["%cycle"], rknee["Mean_Rknee"] - rknee["std_Rknee"], rknee["Mean_Rknee"] + rknee["std_Rknee"])]
    
            ))
            fig4.update_layout(
                title="Right Knee",
                xaxis_title="%Cycle",
                yaxis_title="Value",
                template="plotly_dark",
                title_x=0.5,
                hovermode="x unified"
            )
            


            # Hip
            # Ganti semua variabel pelvis menjadi hip
            l_hip_angles = pd.DataFrame(filtered_df['LHipAngles_X'].tolist())
            r_hip_angles = pd.DataFrame(filtered_df['RHipAngles_X'].tolist())

            l_hip_angles.columns = [f"L_Hip_{i}" for i in range(l_hip_angles.shape[1])]
            r_hip_angles.columns = [f"R_Hip_{i}" for i in range(r_hip_angles.shape[1])]

            mean_l_hip = l_hip_angles.mean(axis=0).values
            std_l_hip = l_hip_angles.std(axis=0) / np.sqrt(l_hip_angles.shape[0])
            mean_r_hip = r_hip_angles.mean(axis=0).values
            std_r_hip = r_hip_angles.std(axis=0) / np.sqrt(r_hip_angles.shape[0])

            std_l_hip = std_l_hip.values if isinstance(std_l_hip, pd.Series) else std_l_hip
            std_r_hip = std_r_hip.values if isinstance(std_r_hip, pd.Series) else std_r_hip

            lhip = pd.DataFrame({
                "%cycle": list(range(101)),
                'Mean_Lhip': mean_l_hip,
                'std_Lhip': std_l_hip,
                'your left hip': norm_kinematics_df['LHipAngles_X']
            })
            
            rhip = pd.DataFrame({
                "%cycle": list(range(101)),
                'Mean_Rhip': mean_r_hip,
                'std_Rhip': std_r_hip,
                'your right hip': norm_kinematics_df['RHipAngles_X']
            })

            fig5 = go.Figure()

            fig5.add_trace(go.Scatter(
                x=lhip["%cycle"], 
                y=lhip["Mean_Lhip"], 
                mode='lines',
                name='Average Left Hip<br>(Normal Subjects)',
                line=dict(color='orange'),
                hoverinfo='text',
                text=[f"Average Normal Subjects: {cycle}%, {val:.2f}°" for cycle, val in zip(lhip["%cycle"], lhip["Mean_Lhip"])]
            ))
            fig5.add_trace(go.Scatter(
                x=lhip["%cycle"], 
                y=lhip["your left hip"], 
                mode='lines',
                name='Patient',
                line=dict(color='black')
            ))
            fig5.add_trace(go.Scatter(
                x=lhip["%cycle"], 
                y=lhip["Mean_Lhip"] + lhip["std_Lhip"], 
                mode='lines',
                name='Upper Bound (Left)',
                line=dict(color='orange', width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
            fig5.add_trace(go.Scatter(
                x=lhip["%cycle"], 
                y=lhip["Mean_Lhip"] - lhip["std_Lhip"], 
                mode='lines',
                name='Standard Error Area',
                line=dict(color='orange', width=0),
                fill='tonexty',
                fillcolor='rgba(255, 165, 0, 0.2)',
                showlegend=False,
                hoverinfo='text',
                text=[f"Upper Bound (Left): {cycle}%, {valup:.2f}°<br>Lower Bound (Left): {cycle}%, {vallow:.2f}°" for cycle, vallow, valup in zip(lhip["%cycle"], lhip["Mean_Lhip"] - lhip["std_Lhip"], lhip["Mean_Lhip"] + lhip["std_Lhip"])]
    
            ))
            fig5.update_layout(
                title="Left Hip",
                xaxis_title="%Cycle",
                yaxis_title="Value",
                template="plotly_dark",
                title_x=0.5,
                hovermode="x unified"
            )
            
            fig6 = go.Figure()
            
            fig6.add_trace(go.Scatter(
                x=rhip["%cycle"], 
                y=rhip["Mean_Rhip"], 
                mode='lines',
                name='Average Right Hip<br>(Normal Subjects)',
                line=dict(color='dark blue'),
                hoverinfo='text',
                text=[f"Average Normal Subjects: {cycle}%, {val:.2f}°" for cycle, val in zip(rhip["%cycle"], rhip["Mean_Rhip"])]
            ))
            fig6.add_trace(go.Scatter(
                x=rhip["%cycle"], 
                y=rhip["your right hip"], 
                mode='lines',
                name='Patient',
                line=dict(color='black')
            ))
            fig6.add_trace(go.Scatter(
                x=rhip["%cycle"], 
                y=rhip["Mean_Rhip"] + rhip["std_Rhip"], 
                mode='lines',
                name='Upper Bound (Right)',
                line=dict(color='dark blue', width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
            fig6.add_trace(go.Scatter(
                x=rhip["%cycle"], 
                y=rhip["Mean_Rhip"] - rhip["std_Rhip"], 
                mode='lines',
                name='Standard Error Area',
                line=dict(color='dark blue', width=0),
                fill='tonexty',
                fillcolor='rgba(0, 255, 255, 0.2)',
                showlegend=False,
                hoverinfo='text',
                text=[f"Upper Bound (Right): {cycle}%, {valup:.2f}°<br>Lower Bound (Right): {cycle}%, {vallow:.2f}°" for cycle, vallow, valup in zip(rhip["%cycle"], rhip["Mean_Rhip"] - rhip["std_Rhip"], rhip["Mean_Rhip"] + rhip["std_Rhip"])]
    
            ))
    
            fig6.update_layout(
                title="Right Hip",
                xaxis_title="%Cycle",
                yaxis_title="Value",
                template="plotly_dark",
                title_x=0.5,
                hovermode="x unified"
            )

            # Ankle
            # Ganti semua variabel pelvis menjadi ankle
            l_ankle_angles = pd.DataFrame(filtered_df['LAnkleAngles_X'].tolist())
            r_ankle_angles = pd.DataFrame(filtered_df['RAnkleAngles_X'].tolist())

            l_ankle_angles.columns = [f"L_Ankle_{i}" for i in range(l_ankle_angles.shape[1])]
            r_ankle_angles.columns = [f"R_Ankle_{i}" for i in range(r_ankle_angles.shape[1])]

            mean_l_ankle = l_ankle_angles.mean(axis=0).values
            std_l_ankle = l_ankle_angles.std(axis=0) / np.sqrt(l_ankle_angles.shape[0])
            mean_r_ankle = r_ankle_angles.mean(axis=0).values
            std_r_ankle = r_ankle_angles.std(axis=0) / np.sqrt(r_ankle_angles.shape[0])

            std_l_ankle = std_l_ankle.values if isinstance(std_l_ankle, pd.Series) else std_l_ankle
            std_r_ankle = std_r_ankle.values if isinstance(std_r_ankle, pd.Series) else std_r_ankle

            lankle = pd.DataFrame({
                "%cycle": list(range(101)),
                'Mean_Lankle': mean_l_ankle,
                'std_Lankle': std_l_ankle,
                'your left ankle': norm_kinematics_df['LAnkleAngles_X']
            })

            rankle = pd.DataFrame({
                "%cycle": list(range(101)),
                'Mean_Rankle': mean_r_ankle,
                'std_Rankle': std_r_ankle,
                'your right ankle': norm_kinematics_df['RAnkleAngles_X']
            })
            
            fig7 = go.Figure()

            fig7.add_trace(go.Scatter(
                x=lankle["%cycle"], 
                y=lankle["Mean_Lankle"], 
                mode='lines',
                name='Average Left Ankle<br>(Normal Subjects)',
                line=dict(color='orange'),
                hoverinfo='text',
                text=[f"Average Normal Subjects: {cycle}%, {val:.2f}°" for cycle, val in zip(lankle["%cycle"], lankle["Mean_Lankle"])]
            ))
            fig7.add_trace(go.Scatter(
                x=lankle["%cycle"], 
                y=lankle["your left ankle"], 
                mode='lines',
                name='Patient',
                line=dict(color='black')
            ))
            fig7.add_trace(go.Scatter(
                x=lankle["%cycle"], 
                y=lankle["Mean_Lankle"] + lankle["std_Lankle"], 
                mode='lines',
                name='Upper Bound (Left)',
                line=dict(color='orange', width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
            fig7.add_trace(go.Scatter(
                x=lankle["%cycle"], 
                y=lankle["Mean_Lankle"] - lankle["std_Lankle"], 
                mode='lines',
                name='Standard Error Area',
                line=dict(color='orange', width=0),
                fill='tonexty',
                fillcolor='rgba(255, 165, 0, 0.2)',
                showlegend=False,
                hoverinfo='text',
                text=[f"Upper Bound (Left): {cycle}%, {valup:.2f}°<br>Lower Bound (Left): {cycle}%, {vallow:.2f}°" for cycle, vallow, valup in zip(lankle["%cycle"], lankle["Mean_Lankle"] - lankle["std_Lankle"], lankle["Mean_Lankle"] + lankle["std_Lankle"])]
    
            ))
            
            fig7.update_layout(
                title="Left Ankle",
                xaxis_title="%Cycle",
                yaxis_title="Value",
                template="plotly_dark",
                title_x=0.5,
                hovermode="x unified"
            )

            fig8 = go.Figure()
            fig8.add_trace(go.Scatter(
                x=rankle["%cycle"], 
                y=rankle["Mean_Rankle"], 
                mode='lines',
                name='Average Right Ankle<br>(Normal Subjects)',
                line=dict(color='dark blue'),
                hoverinfo='text',
                text=[f"Average Normal Subjects: {cycle}%, {val:.2f}°" for cycle, val in zip(rankle["%cycle"], rankle["Mean_Rankle"])]
            ))
            fig8.add_trace(go.Scatter(
                x=rankle["%cycle"], 
                y=rankle["your right ankle"], 
                mode='lines',
                name='Patient',
                line=dict(color='black')
            ))
            fig8.add_trace(go.Scatter(
                x=rankle["%cycle"], 
                y=rankle["Mean_Rankle"] + rankle["std_Rankle"], 
                mode='lines',
                name='Upper Bound (Right)',
                line=dict(color='dark blue', width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
            fig8.add_trace(go.Scatter(
                x=rankle["%cycle"], 
                y=rankle["Mean_Rankle"] - rankle["std_Rankle"], 
                mode='lines',
                name='Standard Error Area',
                line=dict(color='dark blue', width=0),
                fill='tonexty',
                fillcolor='rgba(0, 255, 255, 0.2)',
                showlegend=False,
                hoverinfo='text',
                text=[f"Upper Bound (Right): {cycle}%, {valup:.2f}°<br>Lower Bound (Right): {cycle}%, {vallow:.2f}°" for cycle, vallow, valup in zip(rankle["%cycle"], rankle["Mean_Rankle"] - rankle["std_Rankle"], rankle["Mean_Rankle"] + rankle["std_Rankle"])]
            ))
    
            fig8.update_layout(
                title="Right Ankle",
                xaxis_title="%Cycle",
                yaxis_title="Value",
                template="plotly_dark",
                title_x=0.5,
                hovermode="x unified"
            )
            tab1, tab2, tab3, tab4 = st.tabs(["PELVIS", "KNEE","HIP","ANKLE"])
            data = np.random.randn(10, 1)
            
            with tab1:
                tab1.subheader("PELVIS")
                tab1.write(
                    'Pelvis (dalam bahasa Indonesia: panggul) adalah struktur tulang yang berbentuk cekungan di bawah perut, '
                    'di antara tulang pinggul, dan di atas paha.'
                )
            
                maelpelvis = np.mean(np.abs(lpelvis["your left pelvis"] - lpelvis["Mean_Lpelvis"]))
                maerpelvis = np.mean(np.abs(rpelvis["your right pelvis"] - rpelvis["Mean_Rpelvis"]))
            
                col1, col2 = tab1.columns(2)
                with col1:
                    st.plotly_chart(fig1, use_container_width=True)
                    st.write(f"**Mean difference in left pelvis angle (Patient vs Normal): {maelpelvis:.2f}°**")
            
                    # Statistik tambahan untuk LLM
                    mean_diff_lpelvis = np.mean(lpelvis["your left pelvis"] - lpelvis["Mean_Lpelvis"])
                    std_diff_lpelvis = np.std(lpelvis["your left pelvis"] - lpelvis["Mean_Lpelvis"])
            
                    # Analisis otomatis dengan IBM Granite
                    with st.spinner("Menganalisis pola gerak (Left Pelvis) menggunakan IBM Granite..."):
                        analysis_text_lpelvis = analyze_graph_with_llm("Left Pelvis", maelpelvis, mean_diff_lpelvis, std_diff_lpelvis)
                    st.info(analysis_text_lpelvis)
            
                with col2:
                    st.plotly_chart(fig2, use_container_width=True)
                    st.write(f"**Mean difference in right pelvis angle (Patient vs Normal): {maerpelvis:.2f}°**")
            
                    mean_diff_rpelvis = np.mean(rpelvis["your right pelvis"] - rpelvis["Mean_Rpelvis"])
                    std_diff_rpelvis = np.std(rpelvis["your right pelvis"] - rpelvis["Mean_Rpelvis"])
            
                    with st.spinner("Menganalisis pola gerak (Right Pelvis) menggunakan IBM Granite..."):
                        analysis_text_rpelvis = analyze_graph_with_llm("Right Pelvis", maerpelvis, mean_diff_rpelvis, std_diff_rpelvis)
                    st.info(analysis_text_rpelvis)
                    
            with tab2:
                tab2.subheader("KNEE")
                tab2.write(
                    'Knee (dalam bahasa Indonesia: lutut) adalah bagian tubuh manusia yang terletak di antara paha dan betis, '
                    'berfungsi sebagai sendi yang menghubungkan tulang femur (paha) dengan tulang tibia (betis).'
                )
                maelknee = np.mean(np.abs(lknee["your left knee"] - lknee["Mean_Lknee"]))
                maerknee = np.mean(np.abs(rknee["your right knee"] - rknee["Mean_Rknee"]))
                col1, col2 = tab2.columns(2)  # Membuat 2 kolom di dalam tab2
                with col1:
                    st.plotly_chart(fig3, use_container_width=True)
                    st.write(f"**Mean difference in left knee angle (Patient vs Normal): {maelknee:.2f}°**")
            
                    # Statistik tambahan untuk LLM
                    mean_diff_lknee = np.mean(lknee["your left knee"] - lknee["Mean_Lknee"])
                    std_diff_lknee = np.std(lknee["your left knee"] - lknee["Mean_Lknee"])
            
                    # Analisis otomatis dengan IBM Granite
                    with st.spinner("Menganalisis pola gerak (Left Knee) menggunakan IBM Granite..."):
                        analysis_text_lknee = analyze_graph_with_llm("Left Knee", maelknee, mean_diff_lknee, std_diff_lknee)
                    st.info(analysis_text_lknee)
            
                with col2:
                    st.plotly_chart(fig4, use_container_width=True)
                    st.write(f"**Mean difference in right knee angle (Patient vs Normal): {maerknee:.2f}°**")
            
                    mean_diff_rknee = np.mean(rknee["your right knee"] - rknee["Mean_Rknee"])
                    std_diff_rknee = np.std(rknee["your right knee"] - rknee["Mean_Rknee"])
            
                    with st.spinner("Menganalisis pola gerak (Right Knee) menggunakan IBM Granite..."):
                        analysis_text_rknee = analyze_graph_with_llm("Right Knee", maerknee, mean_diff_rknee, std_diff_rknee)
                    st.info(analysis_text_rknee)
    
            with tab3:
                tab3.subheader("HIP")
                tab3.write(
                    'Hip (dalam bahasa Indonesia: pinggul) adalah bagian tubuh yang terletak di bawah perut, menghubungkan tubuh bagian atas dengan kaki.'
                )
                maelhip = np.mean(np.abs(lhip["your left hip"] - lhip["Mean_Lhip"]))
                maerhip = np.mean(np.abs(rhip["your right hip"] - rhip["Mean_Rhip"]))
                col1, col2 = tab3.columns(2)  # Membuat 2 kolom di dalam tab3
                with col1:
                    st.plotly_chart(fig3, use_container_width=True)
                    st.write(f"**Mean difference in left hip angle (Patient vs Normal): {maelhip:.2f}°**")
            
                    # Statistik tambahan untuk LLM
                    mean_diff_lhip = np.mean(lhip["your left hip"] - lhip["Mean_Lhip"])
                    std_diff_lhip = np.std(lhip["your left hip"] - lhip["Mean_Lhip"])
            
                    # Analisis otomatis dengan IBM Granite
                    with st.spinner("Menganalisis pola gerak (Left hip) menggunakan IBM Granite..."):
                        analysis_text_lhip = analyze_graph_with_llm("Left hip", maelhip, mean_diff_lhip, std_diff_lhip)
                    st.info(analysis_text_lhip)
            
                with col2:
                    st.plotly_chart(fig4, use_container_width=True)
                    st.write(f"**Mean difference in right hip angle (Patient vs Normal): {maerhip:.2f}°**")
            
                    mean_diff_rhip = np.mean(rhip["your right hip"] - rhip["Mean_Rhip"])
                    std_diff_rhip = np.std(rhip["your right hip"] - rhip["Mean_Rhip"])
            
                    with st.spinner("Menganalisis pola gerak (Right hip) menggunakan IBM Granite..."):
                        analysis_text_rhip = analyze_graph_with_llm("Right hip", maerhip, mean_diff_rhip, std_diff_rhip)
                    st.info(analysis_text_rhip)
    
            with tab4:
                tab4.subheader("ANKLE")
                tab4.write(
                    'Ankle (dalam bahasa Indonesia: pergelangan kaki) adalah sendi yang terletak di antara kaki bagian bawah (tulang tibia dan fibula) dan bagian atas kaki (tulang talus).'
                )
                maelankle = np.mean(np.abs(lankle["your left ankle"] - lankle["Mean_Lankle"]))
                maerankle = np.mean(np.abs(rankle["your right ankle"] - rankle["Mean_Rankle"]))
                col1, col2 = tab4.columns(2)  # Membuat 2 kolom di dalam tab4
                with col1:
                    st.plotly_chart(fig3, use_container_width=True)
                    st.write(f"**Mean difference in left ankle angle (Patient vs Normal): {maelankle:.2f}°**")
            
                    # Statistik tambahan untuk LLM
                    mean_diff_lankle = np.mean(lankle["your left ankle"] - lankle["Mean_Lankle"])
                    std_diff_lankle = np.std(lankle["your left ankle"] - lankle["Mean_Lankle"])
            
                    # Analisis otomatis dengan IBM Granite
                    with st.spinner("Menganalisis pola gerak (Left ankle) menggunakan IBM Granite..."):
                        analysis_text_lankle = analyze_graph_with_llm("Left ankle", maelankle, mean_diff_lankle, std_diff_lankle)
                    st.info(analysis_text_lankle)
            
                with col2:
                    st.plotly_chart(fig4, use_container_width=True)
                    st.write(f"**Mean difference in right ankle angle (Patient vs Normal): {maerankle:.2f}°**")
            
                    mean_diff_rankle = np.mean(rankle["your right ankle"] - rankle["Mean_Rankle"])
                    std_diff_rankle = np.std(rankle["your right ankle"] - rankle["Mean_Rankle"])
            
                    with st.spinner("Menganalisis pola gerak (Right ankle) menggunakan IBM Granite..."):
                        analysis_text_rankle = analyze_graph_with_llm("Right ankle", maerankle, mean_diff_rankle, std_diff_rankle)
                    st.info(analysis_text_rankle)

            # tab1.subheader("PELVIS")
            # tab1.write('Pelvis(dalam bahasa Indonesia: panggul) adalah struktur tulang yang berbentuk cekungan di bawah perut, di antara tulang pinggul, dan di atas paha.')
            # maelpelvis = np.mean(np.abs(lpelvis["your left pelvis"] - lpelvis["Mean_Lpelvis"]))
            # maerpelvis = np.mean(np.abs(rpelvis["your right pelvis"] - rpelvis["Mean_Rpelvis"]))
            # tab1.plotly_chart(fig1)
            # tab1.write(f"**Mean difference in left pelvis angle (Patient vs Normal): {maelpelvis:.2f}°**")
            # tab1.plotly_chart(fig2)
            # tab1.write(f"**Mean difference in right pelvis angle (Patient vs Normal): {maerpelvis:.2f}°**")

            # tab2.subheader("KNEE")
            # tab2.write('Knee (dalam bahasa Indonesia: lutut) adalah bagian tubuh manusia yang terletak di antara paha dan betis, berfungsi sebagai sendi yang menghubungkan tulang femur (paha) dengan tulang tibia (betis).')
            # maelknee = np.mean(np.abs(lknee["your left knee"] - lknee["Mean_Lknee"]))
            # maerknee = np.mean(np.abs(rknee["your right knee"] - rknee["Mean_Rknee"]))
            # tab2.plotly_chart(fig3)
            # tab2.write(f"**Mean difference in left knee angle (Patient vs Normal): {maelknee:.2f}°**")
            # tab2.plotly_chart(fig4)
            # tab2.write(f"**Mean difference in right knee angle (Patient vs Normal): {maerknee:.2f}°**")

            # tab3.subheader("HIP")
            # tab3.write('Hip (dalam bahasa Indonesia: pinggul) adalah bagian tubuh yang terletak di bawah perut, menghubungkan tubuh bagian atas dengan kaki.')
            # maelhip = np.mean(np.abs(lhip["your left hip"] - lhip["Mean_Lhip"]))
            # maerhip = np.mean(np.abs(rhip["your right hip"] - rhip["Mean_Rhip"]))
            # tab3.plotly_chart(fig5)
            # tab3.write(f"**Mean difference in left hip angle (Patient vs Normal): {maelhip:.2f}°**")
            # tab3.plotly_chart(fig6)
            # tab3.write(f"**Mean difference in right hip angle (Patient vs Normal): {maerhip:.2f}°**")

            # tab4.subheader("ANKLE")
            # tab4.write('Ankle (dalam bahasa Indonesia: pergelangan kaki) adalah sendi yang terletak di antara kaki bagian bawah (tulang tibia dan fibula) dan bagian atas kaki (tulang talus).')
            # maelankle = np.mean(np.abs(lankle["your left ankle"] - lankle["Mean_Lankle"]))
            # maerankle = np.mean(np.abs(rankle["your right ankle"] - rankle["Mean_Rankle"]))
            # tab4.plotly_chart(fig7)
            # tab4.write(f"**Mean difference in left ankle angle (Patient vs Normal): {maelankle:.2f}°**")
            # tab4.plotly_chart(fig8)
            # tab4.write(f"**Mean difference in right ankle angle (Patient vs Normal): {maerankle:.2f}°**")

    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")
else:
    px.defaults.template = 'plotly_dark'
    px.defaults.color_continuous_scale = 'reds'
    # Koneksi ke MongoDB

    # Create a new client and connect to the server
    client = MongoClient(st.secrets["MONGO_URI"])
    # client = MongoClient('mongodb://localhost:27017/')
    db = client['GaitDB']
    collection = db['gait_data']

    # Membaca data dari MongoDB
    cursor = collection.find()  # Mengambil semua dokumen
    data = list(cursor)  # Mengonversi cursor menjadi list
    if len(data) == 0:
        st.error("The database does not have gait analysis data. Please add or upload the data first.")
        st.stop() 
    elif len(data) == 1:
        st.error("The database only has one gait analysis data. Please add or upload the data first.")
        st.stop() 
    # Normalisasi data untuk DataFrame
    df = pd.json_normalize(data)
    # Mengubah nama kolom untuk mempermudah akses
    df.columns = df.columns.str.replace('Trial Information.', '')
    df.columns = df.columns.str.replace('Subject Parameters.', '')
    df.columns = df.columns.str.replace('Body Measurements.', '')
    df.columns = df.columns.str.replace('Norm Kinematics.', '')

    st.title("Dashboard Gait Analysis")
    st.sidebar.title("Filter Data")
    # Filter usia
    min_age = df['Age'].min()
    max_age = df['Age'].max()
    age_range = st.sidebar.slider(
        'Filter by Age Range:',
        min_value=min_age,
        max_value=max_age,
        value=(min_age, max_age)  # Nilai default adalah keseluruhan rentang usia
    )

    # filter BMI
    bmi = ["All BMI Classification"] + list(df["BMI Classification"].value_counts().keys().sort_values())
    classbmi = st.sidebar.selectbox(label="BMI Classification", options=bmi)

    # filter gender
    gender_mapping = {
        "L": "Pria",
        "P": "Wanita"
    }
    df["Gender"] = df["Gender"].map(gender_mapping)
    gend = ["All Gender"] + list(df["Gender"].value_counts().keys().sort_values())
    gender = st.sidebar.selectbox(label="Gender", options=gend)

        
    filtered_df = df[(df['Age'] >= age_range[0]) & (df['Age'] <= age_range[1])]
    if classbmi != "All BMI Classification":
        filtered_df = filtered_df[filtered_df['BMI Classification'] == classbmi]
        if gender != "All Gender":
            filtered_df = filtered_df[filtered_df["Gender"] == gender]

    if gender != "All Gender":
        filtered_df = filtered_df[filtered_df["Gender"] == gender]
        
    if filtered_df.empty:
        st.error(f"There is no data with gender {gender} classified as {classbmi}.")
    else:
        st.sidebar.markdown(f"**Total Records:** {len(filtered_df)}")
        # Pelvis
        percentage_cycle = pd.DataFrame(filtered_df['Percentage of Gait Cycle'].tolist())
        l_pelvis_angles = pd.DataFrame(filtered_df['LPelvisAngles_X'].tolist())
        r_pelvis_angles = pd.DataFrame(filtered_df['RPelvisAngles_X'].tolist())

        percentage_cycle.columns = [f"%cycle_{i}" for i in range(percentage_cycle.shape[1])]
        l_pelvis_angles.columns = [f"L_Pelvis_{i}" for i in range(l_pelvis_angles.shape[1])]
        r_pelvis_angles.columns = [f"R_Pelvis_{i}" for i in range(r_pelvis_angles.shape[1])]

        mean_l_pelvis = l_pelvis_angles.mean(axis=0).values
        std_l_pelvis = l_pelvis_angles.std(axis=0)/np.sqrt(l_pelvis_angles.shape[0])
        mean_r_pelvis = r_pelvis_angles.mean(axis=0).values
        std_r_pelvis = r_pelvis_angles.std(axis=0)/np.sqrt(r_pelvis_angles.shape[0])

        std_l_pelvis = std_l_pelvis.values if isinstance(std_l_pelvis, pd.Series) else std_l_pelvis
        std_r_pelvis = std_r_pelvis.values if isinstance(std_r_pelvis, pd.Series) else std_r_pelvis

        lpelvis = pd.DataFrame({
            "%cycle": list(range(101)),
            'Mean_Lpelvis': mean_l_pelvis,
            'std_Lpelvis': std_l_pelvis
        })

        rpelvis = pd.DataFrame({
            "%cycle": list(range(101)),
            'Mean_Rpelvis': mean_r_pelvis,
            'std_Rpelvis': std_r_pelvis
        })
        
        ## Create the figure
        fig1 = go.Figure()

        ## Add mean and shading for Left Pelvis
        fig1.add_trace(go.Scatter(
            x=lpelvis["%cycle"], 
            y=lpelvis["Mean_Lpelvis"], 
            mode='lines',
            name='Average Left Pelvis<br>(Normal Subjects)',
            line=dict(color='orange'),
            hoverinfo='text',
            text=[f"Average Normal Subjects: {cycle}%, {val:.2f}°" for cycle, val in zip(lpelvis["%cycle"], lpelvis["Mean_Lpelvis"])]
        ))
        fig1.add_trace(go.Scatter(
            x=lpelvis["%cycle"], 
            y=lpelvis["Mean_Lpelvis"] + lpelvis["std_Lpelvis"], 
            mode='lines',
            name='Upper Bound (Left)',
            line=dict(color='orange', width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig1.add_trace(go.Scatter(
            x=lpelvis["%cycle"], 
            y=lpelvis["Mean_Lpelvis"] - lpelvis["std_Lpelvis"], 
            mode='lines',
            name='Standard Error Area',
            line=dict(color='orange', width=0),
            fill='tonexty',  # Fill between this trace and the previous one
            fillcolor='rgba(255, 165, 0, 0.2)',
            showlegend=True,
            hoverinfo='text',
            text=[f"Upper Bound (Left): {cycle}%, {valup:.2f}°<br>Lower Bound (Left): {cycle}%, {vallow:.2f}°" for cycle, vallow, valup in zip(lpelvis["%cycle"], lpelvis["Mean_Lpelvis"] - lpelvis["std_Lpelvis"], lpelvis["Mean_Lpelvis"] + lpelvis["std_Lpelvis"])]

        ))
        
        ## Update layout
        fig1.update_layout(
            title="Left Pelvis",
            xaxis_title="%Cycle",
            yaxis_title="Value",
            template="plotly_dark",
            title_x=0.5,
            hovermode="x unified"
        )
        
        fig2 = go.Figure()
        ## Add mean and shading for Right Pelvis
        fig2.add_trace(go.Scatter(
            x=rpelvis["%cycle"], 
            y=rpelvis["Mean_Rpelvis"], 
            mode='lines',
            name='Average Right Pelvis<br>(Normal Subjects)',
            line=dict(color='dark blue'),
            hoverinfo='text',
            text=[f"Average Normal Subjects: {cycle}%, {val:.2f}°" for cycle, val in zip(rpelvis["%cycle"], rpelvis["Mean_Rpelvis"])]
        ))
        fig2.add_trace(go.Scatter(
            x=rpelvis["%cycle"], 
            y=rpelvis["Mean_Rpelvis"] + rpelvis["std_Rpelvis"], 
            mode='lines',
            name='Upper Bound (Right)',
            line=dict(color='dark blue', width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig2.add_trace(go.Scatter(
            x=rpelvis["%cycle"], 
            y=rpelvis["Mean_Rpelvis"] - rpelvis["std_Rpelvis"], 
            mode='lines',
            name='Standard Error Area',
            line=dict(color='dark blue', width=0),
            fill='tonexty',
            fillcolor='rgba(0, 255, 255, 0.2)',
            showlegend=True,
            hoverinfo='text',
            text=[f"Upper Bound (Right): {cycle}%, {valup:.2f}°<br>Lower Bound (Right): {cycle}%, {vallow:.2f}°" for cycle, vallow, valup in zip(rpelvis["%cycle"], rpelvis["Mean_Rpelvis"] - rpelvis["std_Rpelvis"], rpelvis["Mean_Rpelvis"] + rpelvis["std_Rpelvis"])]

        ))
        fig2.update_layout(
            title="Right Pelvis",
            xaxis_title="%Cycle",
            yaxis_title="Value",
            template="plotly_dark",
            title_x=0.5,
            hovermode="x unified"
        )
        

        # Knee
        percentage_cycle = pd.DataFrame(filtered_df['Percentage of Gait Cycle'].tolist())
        l_knee_angles = pd.DataFrame(filtered_df['LKneeAngles_X'].tolist())
        r_knee_angles = pd.DataFrame(filtered_df['RKneeAngles_X'].tolist())

        percentage_cycle.columns = [f"%cycle_{i}" for i in range(percentage_cycle.shape[1])]
        l_knee_angles.columns = [f"L_Knee_{i}" for i in range(l_knee_angles.shape[1])]
        r_knee_angles.columns = [f"R_Knee_{i}" for i in range(r_knee_angles.shape[1])]

        mean_l_knee = l_knee_angles.mean(axis=0).values
        std_l_knee = l_knee_angles.std(axis=0) / np.sqrt(l_knee_angles.shape[0])
        mean_r_knee = r_knee_angles.mean(axis=0).values
        std_r_knee = r_knee_angles.std(axis=0) / np.sqrt(r_knee_angles.shape[0])

        std_l_knee = std_l_knee.values if isinstance(std_l_knee, pd.Series) else std_l_knee
        std_r_knee = std_r_knee.values if isinstance(std_r_knee, pd.Series) else std_r_knee

        lknee = pd.DataFrame({
            "%cycle": list(range(101)),
            'Mean_Lknee': mean_l_knee,
            'std_Lknee': std_l_knee
        })
        
        rknee = pd.DataFrame({
            "%cycle": list(range(101)),
            'Mean_Rknee': mean_r_knee,
            'std_Rknee': std_r_knee
        })

        fig3 = go.Figure()

        fig3.add_trace(go.Scatter(
            x=lknee["%cycle"], 
            y=lknee["Mean_Lknee"], 
            mode='lines',
            name='Average Left Knee<br>(Normal Subjects)',
            line=dict(color='orange'),
            hoverinfo='text',
            text=[f"Average Normal Subjects: {cycle}%, {val:.2f}°" for cycle, val in zip(lknee["%cycle"], lknee["Mean_Lknee"])]
        ))
        fig3.add_trace(go.Scatter(
            x=lknee["%cycle"], 
            y=lknee["Mean_Lknee"] + lknee["std_Lknee"], 
            mode='lines',
            name='Upper Bound (Left)',
            line=dict(color='orange', width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig3.add_trace(go.Scatter(
            x=lknee["%cycle"], 
            y=lknee["Mean_Lknee"] - lknee["std_Lknee"], 
            mode='lines',
            name='Standard Error Area',
            line=dict(color='orange', width=0),
            fill='tonexty',
            fillcolor='rgba(255, 165, 0, 0.2)',
            showlegend=False,
            hoverinfo='text',
            text=[f"Upper Bound (Left): {cycle}%, {valup:.2f}°<br>Lower Bound (Left): {cycle}%, {vallow:.2f}°" for cycle, vallow, valup in zip(lknee["%cycle"], lknee["Mean_Lknee"] - lknee["std_Lknee"], lknee["Mean_Lknee"] + lknee["std_Lknee"])]

        ))
        
        fig3.update_layout(
            title="Left Knee",
            xaxis_title="%Cycle",
            yaxis_title="Value",
            template="plotly_dark",
            title_x=0.5,
            hovermode="x unified"
        )
        
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(
            x=rknee["%cycle"], 
            y=rknee["Mean_Rknee"], 
            mode='lines',
            name='Average Right Knee<br>(Normal Subjects)',
            line=dict(color='dark blue'),
            hoverinfo='text',
            text=[f"Average Normal Subjects: {cycle}%, {val:.2f}°" for cycle, val in zip(rknee["%cycle"], rknee["Mean_Rknee"])]
        ))
        fig4.add_trace(go.Scatter(
            x=rknee["%cycle"], 
            y=rknee["Mean_Rknee"] + rknee["std_Rknee"], 
            mode='lines',
            name='Upper Bound (Right)',
            line=dict(color='dark blue', width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig4.add_trace(go.Scatter(
            x=rknee["%cycle"], 
            y=rknee["Mean_Rknee"] - rknee["std_Rknee"], 
            mode='lines',
            name='Standard Error Area',
            line=dict(color='dark blue', width=0),
            fill='tonexty',
            fillcolor='rgba(0, 255, 255, 0.2)',
            showlegend=False,
            hoverinfo='text',
            text=[f"Upper Bound (Right): {cycle}%, {valup:.2f}°<br>Lower Bound (Right): {cycle}%, {vallow:.2f}°" for cycle, vallow, valup in zip(rknee["%cycle"], rknee["Mean_Rknee"] - rknee["std_Rknee"], rknee["Mean_Rknee"] + rknee["std_Rknee"])]

        ))
        fig4.update_layout(
            title="Right Knee",
            xaxis_title="%Cycle",
            yaxis_title="Value",
            template="plotly_dark",
            title_x=0.5,
            hovermode="x unified"
        )
        


        # Hip
        # Ganti semua variabel pelvis menjadi hip
        l_hip_angles = pd.DataFrame(filtered_df['LHipAngles_X'].tolist())
        r_hip_angles = pd.DataFrame(filtered_df['RHipAngles_X'].tolist())

        l_hip_angles.columns = [f"L_Hip_{i}" for i in range(l_hip_angles.shape[1])]
        r_hip_angles.columns = [f"R_Hip_{i}" for i in range(r_hip_angles.shape[1])]

        mean_l_hip = l_hip_angles.mean(axis=0).values
        std_l_hip = l_hip_angles.std(axis=0) / np.sqrt(l_hip_angles.shape[0])
        mean_r_hip = r_hip_angles.mean(axis=0).values
        std_r_hip = r_hip_angles.std(axis=0) / np.sqrt(r_hip_angles.shape[0])

        std_l_hip = std_l_hip.values if isinstance(std_l_hip, pd.Series) else std_l_hip
        std_r_hip = std_r_hip.values if isinstance(std_r_hip, pd.Series) else std_r_hip

        lhip = pd.DataFrame({
            "%cycle": list(range(101)),
            'Mean_Lhip': mean_l_hip,
            'std_Lhip': std_l_hip
        })
        
        rhip = pd.DataFrame({
            "%cycle": list(range(101)),
            'Mean_Rhip': mean_r_hip,
            'std_Rhip': std_r_hip
        })

        fig5 = go.Figure()

        fig5.add_trace(go.Scatter(
            x=lhip["%cycle"], 
            y=lhip["Mean_Lhip"], 
            mode='lines',
            name='Average Left Hip<br>(Normal Subjects)',
            line=dict(color='orange'),
            hoverinfo='text',
            text=[f"Average Normal Subjects: {cycle}%, {val:.2f}°" for cycle, val in zip(lhip["%cycle"], lhip["Mean_Lhip"])]
        ))
        fig5.add_trace(go.Scatter(
            x=lhip["%cycle"], 
            y=lhip["Mean_Lhip"] + lhip["std_Lhip"], 
            mode='lines',
            name='Upper Bound (Left)',
            line=dict(color='orange', width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig5.add_trace(go.Scatter(
            x=lhip["%cycle"], 
            y=lhip["Mean_Lhip"] - lhip["std_Lhip"], 
            mode='lines',
            name='Standard Error Area',
            line=dict(color='orange', width=0),
            fill='tonexty',
            fillcolor='rgba(255, 165, 0, 0.2)',
            showlegend=False,
            hoverinfo='text',
            text=[f"Upper Bound (Left): {cycle}%, {valup:.2f}°<br>Lower Bound (Left): {cycle}%, {vallow:.2f}°" for cycle, vallow, valup in zip(lhip["%cycle"], lhip["Mean_Lhip"] - lhip["std_Lhip"], lhip["Mean_Lhip"] + lhip["std_Lhip"])]

        ))
        fig5.update_layout(
            title="Left Hip",
            xaxis_title="%Cycle",
            yaxis_title="Value",
            template="plotly_dark",
            title_x=0.5,
            hovermode="x unified"
        )
        
        fig6 = go.Figure()
        
        fig6.add_trace(go.Scatter(
            x=rhip["%cycle"], 
            y=rhip["Mean_Rhip"], 
            mode='lines',
            name='Average Right Hip<br>(Normal Subjects)',
            line=dict(color='dark blue'),
            hoverinfo='text',
            text=[f"Average Normal Subjects: {cycle}%, {val:.2f}°" for cycle, val in zip(rhip["%cycle"], rhip["Mean_Rhip"])]
        ))
        fig6.add_trace(go.Scatter(
            x=rhip["%cycle"], 
            y=rhip["Mean_Rhip"] + rhip["std_Rhip"], 
            mode='lines',
            name='Upper Bound (Right)',
            line=dict(color='dark blue', width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig6.add_trace(go.Scatter(
            x=rhip["%cycle"], 
            y=rhip["Mean_Rhip"] - rhip["std_Rhip"], 
            mode='lines',
            name='Standard Error Area',
            line=dict(color='dark blue', width=0),
            fill='tonexty',
            fillcolor='rgba(0, 255, 255, 0.2)',
            showlegend=False,
            hoverinfo='text',
            text=[f"Upper Bound (Right): {cycle}%, {valup:.2f}°<br>Lower Bound (Right): {cycle}%, {vallow:.2f}°" for cycle, vallow, valup in zip(rhip["%cycle"], rhip["Mean_Rhip"] - rhip["std_Rhip"], rhip["Mean_Rhip"] + rhip["std_Rhip"])]

        ))

        fig6.update_layout(
            title="Right Hip",
            xaxis_title="%Cycle",
            yaxis_title="Value",
            template="plotly_dark",
            title_x=0.5,
            hovermode="x unified"
        )

        # Ankle
        # Ganti semua variabel pelvis menjadi ankle
        l_ankle_angles = pd.DataFrame(filtered_df['LAnkleAngles_X'].tolist())
        r_ankle_angles = pd.DataFrame(filtered_df['RAnkleAngles_X'].tolist())

        l_ankle_angles.columns = [f"L_Ankle_{i}" for i in range(l_ankle_angles.shape[1])]
        r_ankle_angles.columns = [f"R_Ankle_{i}" for i in range(r_ankle_angles.shape[1])]

        mean_l_ankle = l_ankle_angles.mean(axis=0).values
        std_l_ankle = l_ankle_angles.std(axis=0) / np.sqrt(l_ankle_angles.shape[0])
        mean_r_ankle = r_ankle_angles.mean(axis=0).values
        std_r_ankle = r_ankle_angles.std(axis=0) / np.sqrt(r_ankle_angles.shape[0])

        std_l_ankle = std_l_ankle.values if isinstance(std_l_ankle, pd.Series) else std_l_ankle
        std_r_ankle = std_r_ankle.values if isinstance(std_r_ankle, pd.Series) else std_r_ankle

        lankle = pd.DataFrame({
            "%cycle": list(range(101)),
            'Mean_Lankle': mean_l_ankle,
            'std_Lankle': std_l_ankle
        })

        rankle = pd.DataFrame({
            "%cycle": list(range(101)),
            'Mean_Rankle': mean_r_ankle,
            'std_Rankle': std_r_ankle
        })
        
        fig7 = go.Figure()

        fig7.add_trace(go.Scatter(
            x=lankle["%cycle"], 
            y=lankle["Mean_Lankle"], 
            mode='lines',
            name='Average Left Ankle<br>(Normal Subjects)',
            line=dict(color='orange'),
            hoverinfo='text',
            text=[f"Average Normal Subjects: {cycle}%, {val:.2f}°" for cycle, val in zip(lankle["%cycle"], lankle["Mean_Lankle"])]
        ))
        fig7.add_trace(go.Scatter(
            x=lankle["%cycle"], 
            y=lankle["Mean_Lankle"] + lankle["std_Lankle"], 
            mode='lines',
            name='Upper Bound (Left)',
            line=dict(color='orange', width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig7.add_trace(go.Scatter(
            x=lankle["%cycle"], 
            y=lankle["Mean_Lankle"] - lankle["std_Lankle"], 
            mode='lines',
            name='Standard Error Area',
            line=dict(color='orange', width=0),
            fill='tonexty',
            fillcolor='rgba(255, 165, 0, 0.2)',
            showlegend=False,
            hoverinfo='text',
            text=[f"Upper Bound (Left): {cycle}%, {valup:.2f}°<br>Lower Bound (Left): {cycle}%, {vallow:.2f}°" for cycle, vallow, valup in zip(lankle["%cycle"], lankle["Mean_Lankle"] - lankle["std_Lankle"], lankle["Mean_Lankle"] + lankle["std_Lankle"])]

        ))
        
        fig7.update_layout(
            title="Left Ankle",
            xaxis_title="%Cycle",
            yaxis_title="Value",
            template="plotly_dark",
            title_x=0.5,
            hovermode="x unified"
        )

        fig8 = go.Figure()
        fig8.add_trace(go.Scatter(
            x=rankle["%cycle"], 
            y=rankle["Mean_Rankle"], 
            mode='lines',
            name='Average Right Ankle<br>(Normal Subjects)',
            line=dict(color='dark blue'),
            hoverinfo='text',
            text=[f"Average Normal Subjects: {cycle}%, {val:.2f}°" for cycle, val in zip(rankle["%cycle"], rankle["Mean_Rankle"])]
        ))
        fig8.add_trace(go.Scatter(
            x=rankle["%cycle"], 
            y=rankle["Mean_Rankle"] + rankle["std_Rankle"], 
            mode='lines',
            name='Upper Bound (Right)',
            line=dict(color='dark blue', width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig8.add_trace(go.Scatter(
            x=rankle["%cycle"], 
            y=rankle["Mean_Rankle"] - rankle["std_Rankle"], 
            mode='lines',
            name='Standard Error Area',
            line=dict(color='dark blue', width=0),
            fill='tonexty',
            fillcolor='rgba(0, 255, 255, 0.2)',
            showlegend=False,
            hoverinfo='text',
            text=[f"Upper Bound (Right): {cycle}%, {valup:.2f}°<br>Lower Bound (Right): {cycle}%, {vallow:.2f}°" for cycle, vallow, valup in zip(rankle["%cycle"], rankle["Mean_Rankle"] - rankle["std_Rankle"], rankle["Mean_Rankle"] + rankle["std_Rankle"])]
        ))

        fig8.update_layout(
            title="Left Ankle",
            xaxis_title="%Cycle",
            yaxis_title="Value",
            template="plotly_dark",
            title_x=0.5,
            hovermode="x unified"
        )
        tab1, tab2, tab3, tab4 = st.tabs(["PELVIS", "KNEE","HIP","ANKLE"])
        data = np.random.randn(10, 1)

        with tab1:
            tab1.subheader("PELVIS")
            tab1.write(
                'Pelvis (dalam bahasa Indonesia: panggul) adalah struktur tulang yang berbentuk cekungan di bawah perut, '
                'di antara tulang pinggul, dan di atas paha.'
            )
            
            col1, col2 = tab1.columns(2)  # Membuat 2 kolom di dalam tab1
            with col1:
                st.plotly_chart(fig1, use_container_width=True)
            with col2:
                st.plotly_chart(fig2, use_container_width=True)
                
        with tab2:
            tab2.subheader("KNEE")
            tab2.write(
                'Knee (dalam bahasa Indonesia: lutut) adalah bagian tubuh manusia yang terletak di antara paha dan betis, '
                'berfungsi sebagai sendi yang menghubungkan tulang femur (paha) dengan tulang tibia (betis).'
            )
            
            col1, col2 = tab2.columns(2)  # Membuat 2 kolom di dalam tab2
            with col1:
                st.plotly_chart(fig3, use_container_width=True)
            with col2:
                st.plotly_chart(fig4, use_container_width=True)

        with tab3:
            tab3.subheader("HIP")
            tab3.write(
                'Hip (dalam bahasa Indonesia: pinggul) adalah bagian tubuh yang terletak di bawah perut, menghubungkan tubuh bagian atas dengan kaki.'
            )
            
            col1, col2 = tab3.columns(2)  # Membuat 2 kolom di dalam tab3
            with col1:
                st.plotly_chart(fig5, use_container_width=True)
            with col2:
                st.plotly_chart(fig6, use_container_width=True)

        with tab4:
            tab4.subheader("ANKLE")
            tab4.write(
                'Ankle (dalam bahasa Indonesia: pergelangan kaki) adalah sendi yang terletak di antara kaki bagian bawah (tulang tibia dan fibula) dan bagian atas kaki (tulang talus).'
            )
            
            col1, col2 = tab4.columns(2)  # Membuat 2 kolom di dalam tab4
            with col1:
                st.plotly_chart(fig7, use_container_width=True)
            with col2:
                st.plotly_chart(fig8, use_container_width=True)
        # tab1.subheader("PELVIS")
        # tab1.write('Pelvis(dalam bahasa Indonesia: panggul) adalah struktur tulang yang berbentuk cekungan di bawah perut, di antara tulang pinggul, dan di atas paha.')
        # tab1.plotly_chart(fig1)
        # tab1.plotly_chart(fig2)

        # tab2.subheader("KNEE")
        # tab2.write('Knee (dalam bahasa Indonesia: lutut) adalah bagian tubuh manusia yang terletak di antara paha dan betis, berfungsi sebagai sendi yang menghubungkan tulang femur (paha) dengan tulang tibia (betis).')
        # tab2.plotly_chart(fig3)
        # tab2.plotly_chart(fig4)

        # tab3.subheader("HIP")
        # tab3.write('Hip (dalam bahasa Indonesia: pinggul) adalah bagian tubuh yang terletak di bawah perut, menghubungkan tubuh bagian atas dengan kaki.')
        # tab3.plotly_chart(fig5)
        # tab3.plotly_chart(fig6)

        # tab4.subheader("ANKLE")
        # tab4.write('Ankle (dalam bahasa Indonesia: pergelangan kaki) adalah sendi yang terletak di antara kaki bagian bawah (tulang tibia dan fibula) dan bagian atas kaki (tulang talus).')
        # tab4.plotly_chart(fig7)
        # tab4.plotly_chart(fig8)
        


