# FarmWise Services Package

# Lazy load ML services to avoid memory issues on startup
ml_service = None
hybrid_service = None

def get_ml_service():
    """Lazy load ML service only when needed"""
    global ml_service
    if ml_service is None:
        try:
            from .ml_model_service import ml_service as _ml_service
            ml_service = _ml_service
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Could not load ML service: {e}")
            ml_service = None
    return ml_service

def get_hybrid_service():
    """Lazy load hybrid service only when needed"""
    global hybrid_service
    if hybrid_service is None:
        try:
            from .hybrid_prediction_service import hybrid_service as _hybrid_service
            hybrid_service = _hybrid_service
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Could not load hybrid service: {e}")
            hybrid_service = None
    return hybrid_service

__all__ = ['get_ml_service', 'get_hybrid_service']
