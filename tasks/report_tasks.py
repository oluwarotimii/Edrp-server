from celery import current_task
from celery_app import celery_app
import logging
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import json

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def generate_pdf_report(self, report_data):
    """Generate PDF reports"""
    try:
        # Update task state to indicate processing
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Starting PDF generation...'}
        )
        
        # Create PDF in memory
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Add content to PDF based on report_data
        p.setFont("Helvetica", 16)
        p.drawString(100, height - 100, report_data.get("title", "Report"))
        
        p.setFont("Helvetica", 12)
        y_position = height - 150
        
        # Add report content
        content = report_data.get("content", "")
        if isinstance(content, str):
            lines = content.split('\\n')
        elif isinstance(content, list):
            lines = content
        else:
            lines = [str(content)]
        
        for line in lines:
            if y_position < 100:  # Start new page if needed
                p.showPage()
                y_position = height - 100
            
            p.drawString(100, y_position, line)
            y_position -= 20
        
        p.save()
        
        # Get PDF data
        buffer.seek(0)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Update task state to completed
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 100, 'total': 100, 'status': 'PDF generation completed'}
        )
        
        # In a real implementation, you would save the PDF to storage
        # and return the file path or URL
        return {
            'status': 'completed',
            'report_id': report_data.get('report_id'),
            'pdf_size': len(pdf_data),
            'message': 'PDF report generated successfully'
        }
        
    except Exception as e:
        logger.error(f"PDF report generation failed: {str(e)}")
        raise
