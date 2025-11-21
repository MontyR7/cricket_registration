import qrcode
import os
from io import BytesIO
import base64

def generate_upi_qr_code(amount, transaction_note, transaction_id):
    """
    Generate a UPI QR code with the specified amount and transaction details.
    Returns the QR code as a base64 encoded string.
    """
    # Get merchant details from environment variables
    upi_id = os.getenv('UPI_ID')
    merchant_name = os.getenv('MERCHANT_NAME')
    merchant_code = os.getenv('MERCHANT_CODE')

    # Construct UPI URI according to UPI specification
    # Format: upi://pay?pa=UPI_ID&pn=MERCHANT_NAME&mc=MERCHANT_CODE&tr=TRANSACTION_ID&am=AMOUNT&tn=NOTE
    upi_uri = f"upi://pay?pa={upi_id}&pn={merchant_name}&mc={merchant_code}&tr={transaction_id}&am={amount}&tn={transaction_note}"

    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    
    # Add data to QR code
    qr.add_data(upi_uri)
    qr.make(fit=True)

    # Create an image from the QR Code
    qr_image = qr.make_image(fill_color="black", back_color="white")

    # Convert the image to base64 string
    buffered = BytesIO()
    qr_image.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    return qr_base64, upi_uri