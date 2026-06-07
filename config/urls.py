from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/envios/', include('envios.urls')),
    
    # Rutas para generar el Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # La interfaz gráfica de Swagger UI
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
