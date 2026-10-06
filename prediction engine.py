
import os
import pickle
import operator
import numpy as np
import pandas as pd
from deap import gp


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Models can be in a "models" folder next to this file, or beside it directly
MODEL_PATH = os.path.join(BASE_DIR, "models")
if not os.path.isdir(MODEL_PATH):
    MODEL_PATH = BASE_DIR


def protected_div(left, right):
    if abs(right) < 1e-6:
        return 1.0
    return left / right


# Load saved models
model_files = {
    "Diabetes": "diabetes_gp_model.pkl",
    "Heart Disease": "heart_gp_model.pkl",
    "Breast Cancer": "breast_cancer_gp_model.pkl",
    "Stroke": "stroke_gp_model.pkl"
}


loaded_models = {}

for disease, filename in model_files.items():

    path = os.path.join(MODEL_PATH, filename)

    with open(path, "rb") as f:
        loaded_models[disease] = pickle.load(f)


def compile_gp_model(model, n_features, name="MODEL"):

    pset = gp.PrimitiveSet(name, n_features)

    pset.addPrimitive(operator.add, 2)
    pset.addPrimitive(operator.sub, 2)
    pset.addPrimitive(operator.mul, 2)
    pset.addPrimitive(protected_div, 2)

    return gp.compile(expr=model, pset=pset)


def predict_with_gp(bundle, input_data):

    model = bundle["model"]
    n_features = bundle["n_features"]
    threshold = bundle["threshold"]
    feature_names = bundle["feature_names"]

    input_df = pd.DataFrame(
        input_data,
        columns=feature_names
    )

    if "scaler" in bundle and bundle["scaler"] is not None:
        processed_data = bundle["scaler"].transform(input_df)
    else:
        processed_data = input_df.to_numpy()

    func = compile_gp_model(
        model,
        n_features,
        bundle["disease"].upper().replace(" ", "_")
    )

    row = processed_data[0]

    result = func(*row)

    if np.isfinite(result):
        prediction = 1 if result >= threshold else 0
    else:
        prediction = 0

    return prediction, result


def preprocess_diabetes_input(data):

    data = data.copy()

    data["Gender"] = data["Gender"].map({
        "Male": 1,
        "Female": 0
    })

    yes_no_columns = [
        "Polyuria",
        "Polydipsia",
        "sudden weight loss",
        "weakness",
        "Polyphagia",
        "Genital thrush",
        "visual blurring",
        "Itching",
        "Irritability",
        "delayed healing",
        "partial paresis",
        "muscle stiffness",
        "Alopecia",
        "Obesity"
    ]

    for column in yes_no_columns:
        data[column] = data[column].map({
            "Yes": 1,
            "No": 0
        })

    return data


def preprocess_heart_input(data):

    data = data.copy()

    data = data[
        [
            "age",
            "sex",
            "cp",
            "trestbps",
            "chol",
            "fbs",
            "restecg",
            "thalach",
            "exang",
            "oldpeak",
            "slope",
            "ca",
            "thal"
        ]
    ]

    return data


def preprocess_breast_cancer_input(data):

    data = data.copy()

    data = data[
        [
            "radius_mean",
            "texture_mean",
            "perimeter_mean",
            "area_mean",
            "smoothness_mean",
            "compactness_mean",
            "concavity_mean",
            "concave_points_mean",
            "symmetry_mean",
            "fractal_dimension_mean",
            "radius_se",
            "texture_se",
            "perimeter_se",
            "area_se",
            "smoothness_se",
            "compactness_se",
            "concavity_se",
            "concave_points_se",
            "symmetry_se",
            "fractal_dimension_se",
            "radius_worst",
            "texture_worst",
            "perimeter_worst",
            "area_worst",
            "smoothness_worst",
            "compactness_worst",
            "concavity_worst",
            "concave_points_worst",
            "symmetry_worst",
            "fractal_dimension_worst"
        ]
    ]

    return data


def preprocess_stroke_input(data):

    data = data.copy()

    data["gender"] = data["gender"].map({
        "Male": 1,
        "Female": 0,
        "Other": 0
    })

    data["ever_married"] = data["ever_married"].map({
        "Yes": 1,
        "No": 0
    })

    data["Residence_type"] = data["Residence_type"].map({
        "Urban": 1,
        "Rural": 0
    })

    data = pd.get_dummies(
        data,
        columns=["work_type", "smoking_status"],
        dtype=int
    )

    feature_names = loaded_models["Stroke"]["feature_names"]

    for column in feature_names:

        if column not in data.columns:
            data[column] = 0

    data = data[feature_names]

    return data


def predict_disease(disease, input_data):

    if disease not in loaded_models:

        raise ValueError(
            f"Unsupported disease: {disease}"
        )

    input_data = input_data.copy()

    if disease == "Diabetes":
        input_data = preprocess_diabetes_input(input_data)

    elif disease == "Heart Disease":
        input_data = preprocess_heart_input(input_data)

    elif disease == "Breast Cancer":
        input_data = preprocess_breast_cancer_input(input_data)

    elif disease == "Stroke":
        input_data = preprocess_stroke_input(input_data)

    bundle = loaded_models[disease]

    prediction, gp_score = predict_with_gp(
        bundle,
        input_data
    )

    target_mapping = bundle["target_mapping"]

    result_label = target_mapping[prediction]

    return {
        "Disease": disease,
        "Prediction": prediction,
        "Result": result_label,
        "GP Score": gp_score
    }
