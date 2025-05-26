from django.http import HttpResponse
from django.views import View
from django.template.loader import render_to_string
from pedidos.models import Pedido
from django.utils.timezone import localtime
import io
from reportlab.pdfgen import canvas
import pdfkit

class ExportarPedidosPDFView(View):
    def get(self, request, *args, **kwargs):
        metodo = self.kwargs.get('metodo', '1')
        if metodo == '2':
            return self.gerar_pdf_pdfkit()
        return self.gerar_pdf_reportlab()

    def gerar_pdf_reportlab(self):
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer)
        pedidos = Pedido.objects.select_related('produto').all()

        y = 800
        p.setFont("Helvetica", 12)
        p.drawString(100, y, "Lista de Pedidos (ReportLab):")
        y -= 30

        for pedido in pedidos:
            texto = f"{localtime(pedido.data_pedido).strftime('%d/%m/%Y %H:%M')} - {pedido.quantidade}x {pedido.produto.nome}"
            p.drawString(100, y, texto)
            y -= 20
            if y < 50:
                p.showPage()
                y = 800

        p.showPage()
        p.save()
        buffer.seek(0)

        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="pedidos_reportlab.pdf"'
        return response

    def gerar_pdf_pdfkit(self):
        pedidos = Pedido.objects.select_related('produto').all()
        html = render_to_string('relatorios/relatorio_pdf.html', {'pedidos': pedidos})
        pdf = pdfkit.from_string(html, False)

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="pedidos_pdfkit.pdf"'
        return response