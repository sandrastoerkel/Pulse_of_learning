import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import pickle
sys.path.append('..')

from utils.db_loader import get_db_connection
from utils.feature_selector import PISAFeatureSelector
from utils.feature_descriptions import get_feature_description_bilingual

from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, mean_absolute_percentage_error
import shap
import plotly.express as px
import plotly.graph_objects as go

# ============================================
# PAGE CONFIG
# ============================================

st.set_page_config(
    page_title="ML Pipeline",
    page_icon="🔬",
    layout="wide"
)

# ============================================
# TITLE
# ============================================

st.title("🔬 Phase 5: ML-Pipeline (XGBoost + SHAP)")
st.markdown("**Wissenschaftliche Feature-Analyse nach Forscher-Standards**")

st.divider()

# ============================================
# WORKFLOW
# ============================================

st.header("📋 Workflow-Übersicht")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 🧹 Step 1: Preprocessing

    - Feature Selection (58 ausgewählte Skalen von 157 im Datensatz)
    - Missing Value Treatment
    - Outlier Check
    - Standardization

    **Output:** X_scaled.pkl, y.pkl
    """)

with col2:
    st.markdown("""
    ### 🎓 Step 2: Training

    - XGBoost Model
    - 5-Fold Cross-Validation
    - Hyperparameter (Forscher-Standard)
    - Performance Evaluation

    **Output:** xgboost_model.pkl
    """)

with col3:
    st.markdown("""
    ### 🔍 Step 3: SHAP Analysis

    - TreeExplainer
    - Feature Importance
    - Top 15 Features
    - Visualizations

    **Output:** feature_importance.csv
    """)

st.divider()

# ============================================
# TAB NAVIGATION
# ============================================

tabs = st.tabs(["🧹 Preprocessing", "🎓 Training", "🔍 SHAP Analysis"])

# ============================================
# TAB 1: PREPROCESSING
# ============================================

with tabs[0]:
    st.header("🧹 Data Preprocessing")

    st.info("""
    **Forscher-Methode (Chinesische PISA-Gruppe 2024):**
    - Fokus auf WLE-Skalen (reliabel, IRT-skaliert)
    - Missing Values: Mode (kategorisch), Median (numerisch)
    - Outliers: KEINE Entfernung (alle Schüler behalten)
    - Scaling: StandardScaler (μ=0, σ=1)
    """)

    # Initialize Feature Selector
    feature_selector = PISAFeatureSelector()

    # Target variable selection
    st.subheader("🎯 Ziel-Variable auswählen")

    target_var = st.selectbox(
        "Welche Kompetenz möchtest du vorhersagen?",
        ["PV1MATH", "PV1READ", "PV1SCIE"],
        format_func=lambda x: {
            "PV1MATH": "📐 Mathematik",
            "PV1READ": "📖 Lesen",
            "PV1SCIE": "🔬 Naturwissenschaften"
        }[x],
        key="target_var_preprocessing"
    )

    # Show selected features
    with st.expander("📊 Ausgewählte Features anzeigen"):
        desired_features = feature_selector.get_all_features(target_var=target_var)

        st.success(f"✅ {len(desired_features)} Features ausgewählt")

        feature_groups = feature_selector.get_feature_groups_display()

        for group_name, group_info in feature_groups.items():
            st.markdown(f"**{group_name}**")
            st.caption(f"{group_info['description']} - {group_info['research_note']}")

            # Show features in columns
            cols = st.columns(4)
            for idx, feature in enumerate(group_info['features']):
                with cols[idx % 4]:
                    st.code(feature, language="")

    st.divider()

    # Check if already preprocessed
    preproc_done = (
        Path("data/X_scaled.pkl").exists() and
        Path("data/y.pkl").exists()
    )

    if preproc_done:
        st.success("✅ Preprocessing bereits durchgeführt!")

        # Load and show stats
        try:
            X_scaled = pd.read_pickle("data/X_scaled.pkl")
            y = pd.read_pickle("data/y.pkl")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Schüler (N)", f"{len(X_scaled):,}")
            with col2:
                st.metric("Features", len(X_scaled.columns))
            with col3:
                st.metric("Target", target_var)

            with st.expander("Feature-Liste anzeigen"):
                st.write(X_scaled.columns.tolist())

        except Exception as e:
            st.error(f"Fehler beim Laden: {e}")

    # Preprocessing button
    if st.button("🔧 Preprocessing durchführen", type="primary", key="do_preprocessing"):
        with st.spinner("Führe Preprocessing durch..."):

            # Load database
            conn = get_db_connection()

            progress_bar = st.progress(0)
            status_text = st.empty()

            # 1. Load data
            status_text.text("1/5 Lade Daten aus Datenbank...")
            progress_bar.progress(0.2)

            query = f"""
            SELECT * FROM student_data
            WHERE CNT = 'DEU' AND {target_var} IS NOT NULL
            """
            df_full = pd.read_sql_query(query, conn)

            st.success(f"✅ {len(df_full):,} Schüler geladen")

            # 2. Feature Selection
            status_text.text("2/5 Wende Feature Selection an...")
            progress_bar.progress(0.4)

            X, y, selected_features, selection_report = feature_selector.select_features(
                df_full,
                target_var=target_var
            )

            st.success(f"✅ {len(selected_features)} Features ausgewählt")

            # 3. Missing Value Treatment
            status_text.text("3/5 Behandle Missing Values...")
            progress_bar.progress(0.6)

            # Remove columns with >50% missing
            missing_threshold = 0.5
            missing_pct = X.isnull().sum() / len(X)
            cols_to_keep = missing_pct[missing_pct < missing_threshold].index.tolist()

            X_clean = X[cols_to_keep].copy()
            removed_cols = len(X.columns) - len(X_clean.columns)

            # Impute remaining missing values
            # Categorical: Mode
            cat_cols = X_clean.select_dtypes(include=['object']).columns
            for col in cat_cols:
                if X_clean[col].isnull().any():
                    mode_value = X_clean[col].mode()[0] if len(X_clean[col].mode()) > 0 else X_clean[col].iloc[0]
                    X_clean[col].fillna(mode_value, inplace=True)

            # Numeric: Median
            num_cols = X_clean.select_dtypes(include=['number']).columns
            for col in num_cols:
                if X_clean[col].isnull().any():
                    median_value = X_clean[col].median()
                    X_clean[col].fillna(median_value, inplace=True)

            st.success(f"✅ {removed_cols} Features entfernt (>50% Missing), Rest imputiert")

            # 4. NO Outlier Removal (Forscher-Standard für PISA)
            status_text.text("4/5 Outlier-Check übersprungen (alle Schüler behalten)...")
            progress_bar.progress(0.8)

            st.success(f"✅ Alle {len(X_clean):,} Schüler behalten (kein Outlier-Removal)")

            # 5. Feature Scaling
            status_text.text("5/5 Standardisiere Features...")
            progress_bar.progress(1.0)

            # Only scale numeric columns
            numeric_features = X_clean.select_dtypes(include=['number']).columns
            X_numeric = X_clean[numeric_features]

            scaler = StandardScaler()
            X_scaled = pd.DataFrame(
                scaler.fit_transform(X_numeric),
                columns=numeric_features,
                index=X_clean.index
            )

            st.success(f"✅ {len(numeric_features)} Features standardisiert")

            # 6. Save
            status_text.text("Speichere Ergebnisse...")

            # Ensure directories exist
            Path("data").mkdir(exist_ok=True)

            X_scaled.to_pickle('data/X_scaled.pkl')
            y.to_pickle('data/y.pkl')
            with open('data/scaler.pkl', 'wb') as f:
                pickle.dump(scaler, f)

            # Save feature names
            with open('data/feature_names.txt', 'w') as f:
                f.write('\n'.join(X_scaled.columns))

            status_text.text("✅ Preprocessing abgeschlossen!")
            progress_bar.progress(1.0)

            # Summary
            st.divider()
            st.subheader("📊 Preprocessing-Zusammenfassung")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Schüler", f"{len(X_scaled):,}")
            with col2:
                st.metric("Features", f"{len(X_scaled.columns):,}")
            with col3:
                st.metric("Missing Values", "0")
            with col4:
                st.metric("Scaling", "μ=0, σ=1")

            st.success("""
            ✅ **Preprocessing abgeschlossen!**

            Gehe zu **Tab 2: Training** um das XGBoost-Modell zu trainieren.
            """)

            conn.close()

            # Trigger rerun to update UI
            st.rerun()

# ============================================
# TAB 2: TRAINING
# ============================================

with tabs[1]:
    st.header("🎓 Model Training")

    # Check prerequisites
    if not (Path('data/X_scaled.pkl').exists() and Path('data/y.pkl').exists()):
        st.warning("⚠️ Führe erst Preprocessing durch (Tab 1)")
    else:
        # Load preprocessed data
        X_scaled = pd.read_pickle('data/X_scaled.pkl')
        y = pd.read_pickle('data/y.pkl')

        st.success(f"✅ Daten geladen: {len(X_scaled):,} Schüler, {len(X_scaled.columns):,} Features")

        st.info("""
        **XGBoost Konfiguration (Forscher-Standard):**
        - n_estimators: 1000
        - learning_rate: 0.01
        - max_depth: 6
        - subsample: 0.8
        - colsample_bytree: 0.8
        - 5-Fold Cross-Validation
        """)

        # Check if model exists
        model_path = Path("models/xgboost_model.pkl")

        if model_path.exists():
            st.success("✅ Modell bereits trainiert!")

            with open(model_path, 'rb') as f:
                model = pickle.load(f)

            st.metric("Modell-Typ", "XGBoost Regressor")

            # Show saved metrics if available
            if 'training_metrics' in st.session_state:
                metrics = st.session_state['training_metrics']

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Test R²", f"{metrics['test_r2']:.4f}")
                with col2:
                    st.metric("Test RMSE", f"{metrics['test_rmse']:.2f}")
                with col3:
                    if 'cv_r2_mean' in metrics:
                        st.metric("CV R² (5-Fold)", f"{metrics['cv_r2_mean']:.4f}")

        # Training button
        if st.button("🎓 Modell trainieren", type="primary", key="do_training"):
            with st.spinner("Trainiere XGBoost-Modell..."):

                from sklearn.model_selection import train_test_split

                progress_bar = st.progress(0)
                status_text = st.empty()

                # 1. Train/Test Split
                status_text.text("1/4 Train/Test Split...")
                progress_bar.progress(0.25)

                X_train, X_test, y_train, y_test = train_test_split(
                    X_scaled, y,
                    test_size=0.2,
                    random_state=42
                )

                st.success(f"✅ Training: {len(X_train):,} | Test: {len(X_test):,}")

                # 2. Initialize model
                status_text.text("2/4 Initialisiere XGBoost...")
                progress_bar.progress(0.5)

                model = XGBRegressor(
                    n_estimators=1000,
                    learning_rate=0.01,
                    max_depth=6,
                    min_child_weight=1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    n_jobs=-1
                )

                # 3. Train
                status_text.text("3/4 Trainiere Model...")
                progress_bar.progress(0.75)

                model.fit(X_train, y_train)

                # Predictions
                y_pred_test = model.predict(X_test)

                # Metrics
                test_r2 = r2_score(y_test, y_pred_test)
                test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
                test_mae = mean_absolute_error(y_test, y_pred_test)
                test_mape = mean_absolute_percentage_error(y_test, y_pred_test) * 100

                # 4. Cross-Validation
                status_text.text("4/4 Cross-Validation (5-Fold)...")
                cv_scores = cross_val_score(
                    model, X_scaled, y,
                    cv=5,
                    scoring='r2',
                    n_jobs=-1
                )

                progress_bar.progress(1.0)
                status_text.text("✅ Training abgeschlossen!")

                # Save model
                Path("models").mkdir(exist_ok=True)
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)

                # Save metrics to session state
                st.session_state['training_metrics'] = {
                    'test_r2': test_r2,
                    'test_rmse': test_rmse,
                    'test_mae': test_mae,
                    'test_mape': test_mape,
                    'cv_r2_mean': cv_scores.mean(),
                    'cv_r2_std': cv_scores.std()
                }

                st.success("✅ **Model erfolgreich trainiert!**")

                # Show metrics
                st.divider()
                st.subheader("📊 Performance-Metriken")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.subheader("🎯 Test Set")
                    st.metric("R²", f"{test_r2:.4f}")
                    st.metric("RMSE", f"{test_rmse:.2f}")
                    st.metric("MAE", f"{test_mae:.2f}")
                    st.metric("MAPE", f"{test_mape:.2f}%")

                with col2:
                    st.subheader("🎯 Cross-Validation")
                    st.metric(
                        "R² (5-Fold Mean)",
                        f"{cv_scores.mean():.4f}",
                        delta=f"± {cv_scores.std():.4f}"
                    )

                with col3:
                    st.subheader("🔬 Forscher-Vergleich")
                    st.markdown("**Chinesische Gruppe:**")
                    st.markdown("- R² = 0.77")
                    st.markdown("- MAPE = 10.25%")

                    r2_diff = test_r2 - 0.77
                    if r2_diff >= -0.05:
                        st.success(f"✅ Δ R² = {r2_diff:+.2f}")
                    else:
                        st.info(f"📊 Δ R² = {r2_diff:+.2f}")

                # Predicted vs Actual plot
                st.divider()
                st.subheader("📈 Predicted vs Actual")

                fig = px.scatter(
                    x=y_test,
                    y=y_pred_test,
                    labels={'x': 'Tatsächliche Werte', 'y': 'Vorhergesagte Werte'},
                    title='Predicted vs Actual (Test Set)',
                    opacity=0.6
                )

                # Add diagonal line
                min_val = min(y_test.min(), y_pred_test.min())
                max_val = max(y_test.max(), y_pred_test.max())
                fig.add_trace(go.Scatter(
                    x=[min_val, max_val],
                    y=[min_val, max_val],
                    mode='lines',
                    name='Perfect Prediction',
                    line=dict(color='red', dash='dash')
                ))

                st.plotly_chart(fig, use_container_width=True)

                st.success("""
                ✅ **Model Training abgeschlossen!**

                Gehe zu **Tab 3: SHAP Analysis** für Feature Importance.
                """)

# ============================================
# TAB 3: SHAP ANALYSIS
# ============================================

with tabs[2]:
    st.header("🔍 SHAP Analysis")

    # Check prerequisites
    if not Path('models/xgboost_model.pkl').exists():
        st.warning("⚠️ Trainiere erst ein Modell (Tab 2)")
    elif not (Path('data/X_scaled.pkl').exists() and Path('data/y.pkl').exists()):
        st.warning("⚠️ Preprocessing-Daten fehlen (Tab 1)")
    else:
        # Load model and data
        with open('models/xgboost_model.pkl', 'rb') as f:
            model = pickle.load(f)

        X_scaled = pd.read_pickle('data/X_scaled.pkl')
        y = pd.read_pickle('data/y.pkl')

        st.success(f"✅ Model und Daten geladen: {len(X_scaled):,} Schüler, {len(X_scaled.columns):,} Features")

        st.info("""
        **SHAP (SHapley Additive exPlanations):**
        - Erklärt jeden Vorhersage-Wert
        - Feature Importance nach Mean |SHAP|
        - Visualisierungen der Top Features
        """)

        # Check if SHAP already computed
        shap_path = Path("outputs/feature_importance.csv")

        if shap_path.exists():
            st.success("✅ SHAP-Analyse bereits durchgeführt!")

            # Load and display
            importance_df = pd.read_csv(shap_path)

            st.subheader("🏆 Top 15 Features")

            top_15 = importance_df.head(15)

            fig = px.bar(
                top_15,
                x='Importance_%',
                y='Feature',
                orientation='h',
                title='Top 15 Feature Importance',
                color='Importance_%',
                color_continuous_scale='Blues'
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=600)
            st.plotly_chart(fig, use_container_width=True)

            # Add descriptions
            display_df = top_15.copy()
            display_df['Rank'] = range(1, len(display_df) + 1)
            display_df['Description'] = display_df['Feature'].apply(get_feature_description_bilingual)
            display_df = display_df[['Rank', 'Feature', 'Description', 'Mean_Abs_SHAP', 'Importance_%']]

            st.dataframe(display_df, use_container_width=True, hide_index=True)

        # SHAP computation button
        if st.button("🔍 SHAP neu berechnen", type="primary", key="do_shap"):
            with st.spinner("Berechne SHAP Values (kann 30-60 Sekunden dauern)..."):

                progress_bar = st.progress(0)
                status_text = st.empty()

                # 1. Sample data (for speed)
                status_text.text("1/3 Samplingiere Daten...")
                progress_bar.progress(0.33)

                sample_size = min(1000, len(X_scaled))
                X_sample = X_scaled.sample(n=sample_size, random_state=42)

                # 2. Create explainer
                status_text.text("2/3 Erstelle SHAP Explainer...")
                progress_bar.progress(0.66)

                explainer = shap.TreeExplainer(model)

                # 3. Calculate SHAP values
                status_text.text("3/3 Berechne SHAP Values...")
                shap_values = explainer.shap_values(X_sample)

                progress_bar.progress(1.0)
                status_text.text("✅ SHAP Values berechnet!")

                # Calculate importance
                mean_abs_shap = np.abs(shap_values).mean(axis=0)

                importance_df = pd.DataFrame({
                    'Feature': X_sample.columns,
                    'Mean_Abs_SHAP': mean_abs_shap
                }).sort_values('Mean_Abs_SHAP', ascending=False)

                importance_df['Importance_%'] = (
                    importance_df['Mean_Abs_SHAP'] / importance_df['Mean_Abs_SHAP'].sum() * 100
                )

                # Save
                Path("outputs").mkdir(exist_ok=True)
                importance_df.to_csv(shap_path, index=False)

                # Also save SHAP values
                np.save('outputs/shap_values.npy', shap_values)
                X_sample.to_pickle('outputs/X_sample.pkl')

                st.success("✅ SHAP-Analyse abgeschlossen!")

                # Display results
                st.divider()
                st.subheader("🏆 Top 15 Features")

                top_15 = importance_df.head(15)

                fig = px.bar(
                    top_15,
                    x='Importance_%',
                    y='Feature',
                    orientation='h',
                    title='Top 15 Feature Importance',
                    color='Importance_%',
                    color_continuous_scale='Blues',
                    text='Importance_%'
                )
                fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=600)
                st.plotly_chart(fig, use_container_width=True)

                # Table with descriptions
                display_df = top_15.copy()
                display_df['Rank'] = range(1, len(display_df) + 1)
                display_df['Description'] = display_df['Feature'].apply(get_feature_description_bilingual)
                display_df = display_df[['Rank', 'Feature', 'Description', 'Mean_Abs_SHAP', 'Importance_%']]
                display_df['Mean_Abs_SHAP'] = display_df['Mean_Abs_SHAP'].round(4)
                display_df['Importance_%'] = display_df['Importance_%'].round(2)

                st.dataframe(display_df, use_container_width=True, hide_index=True)

                st.success("""
                ✅ **SHAP-Analyse abgeschlossen!**

                Gehe zu **Phase 1: Top Features** um die Ergebnisse zu sehen.
                """)

# ============================================
# QUICK ACTION BUTTONS
# ============================================

st.divider()

st.header("⚡ Quick Actions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 Zu Top 15 Features", use_container_width=True):
        st.switch_page("pages/1_📊_Top_Features.py")

with col2:
    if st.button("🔍 Zu Skalen Explorer", use_container_width=True):
        st.switch_page("pages/2_🔍_Skalen_Explorer.py")

with col3:
    if st.button("📝 Zu Einzelfragen", use_container_width=True):
        st.switch_page("pages/3_📝_Einzelfragen.py")

# ============================================
# FOOTER
# ============================================

st.divider()

st.caption("""
📚 **Methodik:** Chinesische PISA-Forscher (2024) | XGBoost + SHAP
🔬 **Validiert:** R² = 0.77, MAPE = 10.25%
""")
