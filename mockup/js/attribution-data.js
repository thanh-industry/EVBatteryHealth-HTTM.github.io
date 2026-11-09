/*
 * Feature attribution data - REAL, not illustrative.
 *
 * The deployed model is Logistic Regression, so a prediction decomposes exactly:
 *
 *     log-odds = intercept + SUM_over_features( coefficient_j * scaled_value_j )
 *     probability = 1 / (1 + exp(-log-odds))
 *
 * Every number below was computed from models/model_bundle.joblib against the
 * exact input snapshot stored in the database for that battery, and each one
 * reconstructs the stored probability to within 1e-6. No approximation method
 * (SHAP, LIME) is needed or used: for a linear model this decomposition IS the
 * explanation.
 *
 * One-hot columns are summed back onto their original categorical feature, so a
 * contribution here is per model input, matching what the specialist typed.
 *
 * `other` is the summed contribution of the remaining features outside the top 8,
 * so intercept + sum(top) + other == logit exactly. It is shown in the UI so the
 * arithmetic visibly closes rather than appearing to lose a remainder.
 */
window.ATTRIBUTION = {
  "intercept": -6.0116,
  "records": {
    "BAT-10008123": {
      "label": "No Failure",
      "prob": 0.000261,
      "logit": -8.2497,
      "other": -1.2812,
      "top": [
        {
          "f": "BMS Warning Count",
          "v": "3",
          "c": 2.436
        },
        {
          "f": "Thermal Runaway Risk Score",
          "v": "5.4",
          "c": -1.4297
        },
        {
          "f": "Abnormal Voltage Events (count)",
          "v": "0",
          "c": -0.7386
        },
        {
          "f": "Battery Stress Index",
          "v": "56.88",
          "c": 0.6408
        },
        {
          "f": "Fleet or Private",
          "v": "Private",
          "c": -0.5977
        },
        {
          "f": "Slow Charge Ratio",
          "v": "0.86",
          "c": -0.4587
        },
        {
          "f": "Thermal Health Score",
          "v": "91.41",
          "c": -0.4156
        },
        {
          "f": "Drive Type",
          "v": "FWD",
          "c": -0.3934
        }
      ]
    },
    "BAT-10000942": {
      "label": "Failure",
      "prob": 0.802963,
      "logit": 1.4049,
      "other": -0.5141,
      "top": [
        {
          "f": "BMS Warning Count",
          "v": "6",
          "c": 6.4846
        },
        {
          "f": "Abnormal Voltage Events (count)",
          "v": "2",
          "c": 1.8304
        },
        {
          "f": "Previous Fault Count",
          "v": "0",
          "c": -1.6134
        },
        {
          "f": "Capacity Loss (%)",
          "v": "30.13",
          "c": 1.2743
        },
        {
          "f": "Battery Stress Index",
          "v": "37.07",
          "c": -0.6975
        },
        {
          "f": "State of Health (%)",
          "v": "69.14",
          "c": 0.6799
        },
        {
          "f": "Fleet or Private",
          "v": "Private",
          "c": -0.5977
        },
        {
          "f": "Battery Health (%)",
          "v": "69.87",
          "c": 0.5701
        }
      ]
    },
    "BAT-10017422": {
      "label": "No Failure",
      "prob": 1.2e-05,
      "logit": -11.3047,
      "other": -1.8777,
      "top": [
        {
          "f": "Previous Fault Count",
          "v": "0",
          "c": -1.6134
        },
        {
          "f": "Capacity Loss (%)",
          "v": "9.99",
          "c": -0.8467
        },
        {
          "f": "Battery Stress Index",
          "v": "59.18",
          "c": 0.7962
        },
        {
          "f": "Abnormal Voltage Events (count)",
          "v": "0",
          "c": -0.7386
        },
        {
          "f": "Fleet or Private",
          "v": "Private",
          "c": -0.5977
        },
        {
          "f": "State of Health (%)",
          "v": "90.11",
          "c": -0.4315
        },
        {
          "f": "Maintenance Score",
          "v": "35.91",
          "c": 0.4295
        },
        {
          "f": "Days Since Last Service",
          "v": "1446.7",
          "c": -0.4132
        }
      ]
    },
    "BAT-10006251": {
      "label": "No Failure",
      "prob": 1e-06,
      "logit": -14.3289,
      "other": -1.9782,
      "top": [
        {
          "f": "Previous Fault Count",
          "v": "0",
          "c": -1.6134
        },
        {
          "f": "Thermal Runaway Risk Score",
          "v": "6.86",
          "c": -1.2781
        },
        {
          "f": "Battery Stress Index",
          "v": "35.42",
          "c": -0.809
        },
        {
          "f": "Abnormal Voltage Events (count)",
          "v": "0",
          "c": -0.7386
        },
        {
          "f": "Fleet or Private",
          "v": "Private",
          "c": -0.5977
        },
        {
          "f": "Thermal Health Score",
          "v": "94.56",
          "c": -0.5383
        },
        {
          "f": "Drive Type",
          "v": "FWD",
          "c": -0.3934
        },
        {
          "f": "Capacity Loss (%)",
          "v": "14.51",
          "c": -0.3707
        }
      ]
    },
    "BAT-10002440": {
      "label": "No Failure",
      "prob": 0.006739,
      "logit": -4.9931,
      "other": -0.6734,
      "top": [
        {
          "f": "Previous Fault Count",
          "v": "0",
          "c": -1.6134
        },
        {
          "f": "Capacity Loss (%)",
          "v": "31.12",
          "c": 1.3786
        },
        {
          "f": "Vehicle Model",
          "v": "e:N1",
          "c": 0.9835
        },
        {
          "f": "Battery Stress Index",
          "v": "60.48",
          "c": 0.884
        },
        {
          "f": "Abnormal Voltage Events (count)",
          "v": "0",
          "c": -0.7386
        },
        {
          "f": "State of Health (%)",
          "v": "68.66",
          "c": 0.7053
        },
        {
          "f": "Thermal Runaway Risk Score",
          "v": "25.82",
          "c": 0.6902
        },
        {
          "f": "Fleet or Private",
          "v": "Private",
          "c": -0.5977
        }
      ]
    },
    "BAT-10011679": {
      "label": "No Failure",
      "prob": 0.00807,
      "logit": -4.8114,
      "other": 0.4979,
      "top": [
        {
          "f": "BMS Warning Count",
          "v": "0",
          "c": -1.6126
        },
        {
          "f": "Capacity Loss (%)",
          "v": "30.13",
          "c": 1.2743
        },
        {
          "f": "Vehicle Model",
          "v": "Tiago EV",
          "c": -0.6928
        },
        {
          "f": "State of Health (%)",
          "v": "69.39",
          "c": 0.6666
        },
        {
          "f": "Fleet or Private",
          "v": "Private",
          "c": -0.5977
        },
        {
          "f": "Battery Health (%)",
          "v": "69.87",
          "c": 0.5701
        },
        {
          "f": "Vehicle Brand",
          "v": "Tata",
          "c": 0.5485
        },
        {
          "f": "Abnormal Voltage Events (count)",
          "v": "1",
          "c": 0.5459
        }
      ]
    },
    "BAT-10008143": {
      "label": "Failure",
      "prob": 0.675204,
      "logit": 0.7318,
      "other": -0.2855,
      "top": [
        {
          "f": "Thermal Runaway Risk Score",
          "v": "62.15",
          "c": 4.4618
        },
        {
          "f": "Thermal Health Score",
          "v": "37.44",
          "c": 1.6876
        },
        {
          "f": "Previous Fault Count",
          "v": "0",
          "c": -1.6134
        },
        {
          "f": "Battery Stress Index",
          "v": "65.6",
          "c": 1.2299
        },
        {
          "f": "State of Health (%)",
          "v": "68.66",
          "c": 0.7053
        },
        {
          "f": "Battery Health (%)",
          "v": "69.03",
          "c": 0.6096
        },
        {
          "f": "Fleet or Private",
          "v": "Private",
          "c": -0.5977
        },
        {
          "f": "Abnormal Voltage Events (count)",
          "v": "1",
          "c": 0.5459
        }
      ]
    },
    "BAT-10010920": {
      "label": "No Failure",
      "prob": 0.000324,
      "logit": -8.0338,
      "other": -1.6392,
      "top": [
        {
          "f": "Thermal Runaway Risk Score",
          "v": "36.67",
          "c": 1.8166
        },
        {
          "f": "Previous Fault Count",
          "v": "0",
          "c": -1.6134
        },
        {
          "f": "Battery Stress Index",
          "v": "68.74",
          "c": 1.442
        },
        {
          "f": "Capacity Loss (%)",
          "v": "10.46",
          "c": -0.7972
        },
        {
          "f": "Abnormal Voltage Events (count)",
          "v": "0",
          "c": -0.7386
        },
        {
          "f": "Thermal Health Score",
          "v": "64.82",
          "c": 0.6206
        },
        {
          "f": "Fleet or Private",
          "v": "Private",
          "c": -0.5977
        },
        {
          "f": "Drive Type",
          "v": "AWD",
          "c": -0.5154
        }
      ]
    }
  }
};
