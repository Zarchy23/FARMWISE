"""
Financial Forecasting Model
Predicts future revenue and expenses based on historical data
"""
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from django.conf import settings


class FinancialForecaster:
    """Forecast financial metrics using time series analysis"""
    
    def __init__(self):
        self.revenue_model = None
        self.expense_model = None
        self.scaler = StandardScaler()
        self.feature_columns = None
        self.model_path = os.path.join(settings.BASE_DIR, 'ml_models', 'financial_forecast_model.pkl')
        self.scaler_path = os.path.join(settings.BASE_DIR, 'ml_models', 'financial_forecast_scaler.pkl')
        
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
    
    def prepare_features(self, df):
        """Prepare time series features for forecasting"""
        from core.ml.data_pipeline import DataPipeline
        
        df = DataPipeline.create_time_series_features(df, 'date', 'amount')
        
        # Select feature columns
        feature_cols = [
            'month', 'day_of_week', 'is_weekend', 'is_month_start', 'is_month_end',
            'amount_lag_1', 'amount_lag_7', 'amount_lag_30',
            'amount_rolling_mean_7', 'amount_rolling_std_7'
        ]
        
        self.feature_columns = [col for col in feature_cols if col in df.columns]
        df[self.feature_columns] = df[self.feature_columns].fillna(0)
        
        return df[self.feature_columns]
    
    def train(self, df=None):
        """Train financial forecasting models"""
        from core.ml.data_pipeline import DataPipeline
        
        if df is None or df.empty:
            df = DataPipeline.get_financial_data()
        
        if df.empty:
            raise ValueError("No training data available")
        
        # Separate revenue and expenses
        revenue_df = df[df['transaction_type'] == 'income'].copy()
        expense_df = df[df['transaction_type'] == 'expense'].copy()
        
        metrics = {}
        
        # Train revenue model
        if not revenue_df.empty:
            X_rev = self.prepare_features(revenue_df)
            y_rev = revenue_df['amount'].values
            
            X_train, X_test, y_train, y_test = train_test_split(
                X_rev, y_rev, test_size=0.2, random_state=42
            )
            
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            self.revenue_model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            self.revenue_model.fit(X_train_scaled, y_train)
            
            y_pred = self.revenue_model.predict(X_test_scaled)
            metrics['revenue'] = {
                'mae': mean_absolute_error(y_test, y_pred),
                'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
                'r2': r2_score(y_test, y_pred)
            }
        
        # Train expense model
        if not expense_df.empty:
            X_exp = self.prepare_features(expense_df)
            y_exp = expense_df['amount'].values
            
            X_train, X_test, y_train, y_test = train_test_split(
                X_exp, y_exp, test_size=0.2, random_state=42
            )
            
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            self.expense_model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            self.expense_model.fit(X_train_scaled, y_train)
            
            y_pred = self.expense_model.predict(X_test_scaled)
            metrics['expense'] = {
                'mae': mean_absolute_error(y_test, y_pred),
                'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
                'r2': r2_score(y_test, y_pred)
            }
        
        self.save()
        return metrics
    
    def forecast(self, days=30, transaction_type='income'):
        """Forecast financial metrics for future days"""
        if self.model is None:
            self.load()
        
        from django.utils import timezone
        from datetime import timedelta
        
        model = self.revenue_model if transaction_type == 'income' else self.expense_model
        if model is None:
            raise ValueError(f"No model trained for {transaction_type}")
        
        forecasts = []
        base_date = timezone.now().date()
        
        for i in range(1, days + 1):
            forecast_date = base_date + timedelta(days=i)
            
            features = {
                'month': forecast_date.month,
                'day_of_week': forecast_date.weekday(),
                'is_weekend': 1 if forecast_date.weekday() >= 5 else 0,
                'is_month_start': 1 if forecast_date.day == 1 else 0,
                'is_month_end': 1 if forecast_date.day >= 28 else 0,
                'amount_lag_1': 0,
                'amount_lag_7': 0,
                'amount_lag_30': 0,
                'amount_rolling_mean_7': 0,
                'amount_rolling_std_7': 0,
            }
            
            df = pd.DataFrame([features])
            X = df[self.feature_columns].fillna(0)
            X_scaled = self.scaler.transform(X)
            
            prediction = model.predict(X_scaled)[0]
            forecasts.append({
                'date': forecast_date.isoformat(),
                'predicted_amount': float(max(0, prediction))
            })
        
        return forecasts
    
    def save(self):
        """Save models and scaler"""
        models = {
            'revenue': self.revenue_model,
            'expense': self.expense_model
        }
        joblib.dump(models, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
        joblib.dump(self.feature_columns,
                    os.path.join(settings.BASE_DIR, 'ml_models', 'financial_features.pkl'))
    
    def load(self):
        """Load models and scaler"""
        if os.path.exists(self.model_path):
            models = joblib.load(self.model_path)
            self.revenue_model = models['revenue']
            self.expense_model = models['expense']
            self.scaler = joblib.load(self.scaler_path)
            self.feature_columns = joblib.load(
                os.path.join(settings.BASE_DIR, 'ml_models', 'financial_features.pkl')
            )
        else:
            raise FileNotFoundError("Model not found. Please train the model first.")
