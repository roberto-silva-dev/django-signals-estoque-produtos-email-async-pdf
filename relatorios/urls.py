from django.urls import path
from .views import ExportarPedidosPDFView

urlpatterns = [
    path('pdf/<str:metodo>', ExportarPedidosPDFView.as_view(), name='exportar_pedidos_pdf'),
]
