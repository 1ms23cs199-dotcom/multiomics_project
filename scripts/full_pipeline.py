import numpy as np
import pandas as pd

# ML
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import StratifiedKFold, cross_val_score

# Balancing + Boosting
from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier

# Quantum
from qiskit_machine_learning.kernels import FidelityQuantumKernel
from qiskit_machine_learning.algorithms import QSVC
from qiskit.circuit.library import zz_feature_map


# =========================
# LOAD DATA
# =========================
def load_data():
    base_path = "data/processed/"

    train = pd.read_csv(base_path + "tb_train_set.csv")
    test = pd.read_csv(base_path + "tb_test_set.csv")

    y_train = train["label_binary"]
    y_test = test["label_binary"]

    X_train = train.drop(columns=["label_binary"])
    X_test = test.drop(columns=["label_binary"])

    X_train = X_train.select_dtypes(include=[np.number])
    X_test = X_test.select_dtypes(include=[np.number])

    print("Initial feature shape:", X_train.shape)

    return X_train, X_test, y_train, y_test


# =========================
# CLEAN
# =========================
def clean_data(X_train, X_test):
    X_train = X_train.fillna(X_train.mean())
    X_test = X_test.fillna(X_test.mean())
    print("After cleaning:", X_train.shape)
    return X_train, X_test


# =========================
# PREPROCESS
# =========================
def preprocess(X_train, X_test):
    scaler = StandardScaler()
    return scaler.fit_transform(X_train), scaler.transform(X_test)


# =========================
# BALANCE
# =========================
def balance_data(X_train, y_train):
    print("Before SMOTE:", np.bincount(y_train))
    smote = SMOTE(random_state=42)
    X_train, y_train = smote.fit_resample(X_train, y_train)
    print("After SMOTE:", np.bincount(y_train))
    return X_train, y_train


# =========================
# CLASSICAL
# =========================
def classical_models(X_train, X_test, y_train, y_test):

    print("\n--- Classical Models ---")

    svm = SVC(kernel='rbf', C=20)
    svm.fit(X_train, y_train)
    print("SVM:", accuracy_score(y_test, svm.predict(X_test)))

    rf = RandomForestClassifier(n_estimators=300, max_depth=15, random_state=42)
    rf.fit(X_train, y_train)
    print("RF:", accuracy_score(y_test, rf.predict(X_test)))


# =========================
# XGBOOST
# =========================
def advanced_model(X_train, X_test, y_train, y_test):

    print("\n--- XGBoost ---")

    model = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
        eval_metric='logloss'
    )

    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    print("XGB:", accuracy_score(y_test, preds))

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    print("CV:", cross_val_score(model, X_train, y_train, cv=cv).mean())


# =========================
# QUANTUM (IMPROVED)
# =========================
def quantum_model(X_train, X_test, y_train, y_test):

    print("\n--- Quantum Model (Improved) ---")

    from sklearn.decomposition import PCA
    from sklearn.preprocessing import MinMaxScaler
    from sklearn.feature_selection import SelectKBest, f_classif

    # 🔥 Feature Selection (important genes)
    selector = SelectKBest(f_classif, k=20)
    X_train_fs = selector.fit_transform(X_train, y_train)
    X_test_fs = selector.transform(X_test)

    # 🔥 PCA (optimized)
    pca = PCA(n_components=8)
    X_train_q = pca.fit_transform(X_train_fs)
    X_test_q = pca.transform(X_test_fs)

    # 🔥 Quantum scaling (VERY IMPORTANT)
    scaler = MinMaxScaler(feature_range=(0, np.pi))
    X_train_q = scaler.fit_transform(X_train_q)
    X_test_q = scaler.transform(X_test_q)

    # 🔥 Use more data (not too small)
    X_train_q = X_train_q[:200]
    y_train_q = y_train[:200]

    # 🔥 Better feature map
    feature_map = zz_feature_map(feature_dimension=8, reps=2)

    kernel = FidelityQuantumKernel(feature_map=feature_map)

    qsvc = QSVC(quantum_kernel=kernel, C=5)

    qsvc.fit(X_train_q, y_train_q)
    preds = qsvc.predict(X_test_q)

    print("Quantum Accuracy:", accuracy_score(y_test, preds))


# =========================
# MAIN
# =========================
def run_pipeline():

    print("🚀 Final Pipeline Running...")

    X_train, X_test, y_train, y_test = load_data()

    X_train, X_test = clean_data(X_train, X_test)

    X_train, X_test = preprocess(X_train, X_test)

    X_train, y_train = balance_data(X_train, y_train)

    classical_models(X_train, X_test, y_train, y_test)

    advanced_model(X_train, X_test, y_train, y_test)

    quantum_model(X_train, X_test, y_train, y_test)

    print("\n✅ DONE")


if __name__ == "__main__":
    run_pipeline()