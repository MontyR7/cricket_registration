function checkUtrValidation(form) {
    const utrNumber = form.utr_number.value;
    if (!utrNumber || utrNumber.trim() === '') {
        alert('Please enter the UPI Transaction Reference (UTR) Number');
        return false;
    }
    
    // Check if browser supports AJAX
    if (!window.XMLHttpRequest) {
        // Fallback to regular form submission for older browsers
        return true;
    }
    
    const formData = new FormData(form);
    const xhr = new XMLHttpRequest();
    
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.success && response.redirect_url) {
                        // Show success modal
                        const modalHtml = `
                            <div class="modal fade" id="paymentSuccessModal" tabindex="-1" aria-hidden="true">
                                <div class="modal-dialog">
                                    <div class="modal-content">
                                        <div class="modal-header bg-success text-white">
                                            <h5 class="modal-title">Payment Successful!</h5>
                                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                                        </div>
                                        <div class="modal-body">
                                            <p>${response.message}</p>
                                        </div>
                                        <div class="modal-footer">
                                            <button type="button" class="btn btn-success" onclick="window.location.href='${response.redirect_url}'">Continue</button>
                                        </div>
                                    </div>
                                </div>
                            </div>`;
                        document.body.insertAdjacentHTML('beforeend', modalHtml);
                        const modal = new bootstrap.Modal(document.getElementById('paymentSuccessModal'));
                        modal.show();
                        document.getElementById('paymentSuccessModal').addEventListener('hidden.bs.modal', function () {
                            window.location.href = response.redirect_url;
                        });
                    } else {
                        // Show error modal
                        const modalHtml = `
                            <div class="modal fade" id="paymentErrorModal" tabindex="-1" aria-hidden="true">
                                <div class="modal-dialog">
                                    <div class="modal-content">
                                        <div class="modal-header bg-danger text-white">
                                            <h5 class="modal-title">Payment Verification Failed</h5>
                                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                                        </div>
                                        <div class="modal-body">
                                            <p>${response.message || 'Payment verification failed. Please try again.'}</p>
                                        </div>
                                        <div class="modal-footer">
                                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                                        </div>
                                    </div>
                                </div>
                            </div>`;
                        document.body.insertAdjacentHTML('beforeend', modalHtml);
                        const modal = new bootstrap.Modal(document.getElementById('paymentErrorModal'));
                        modal.show();
                        document.getElementById('verifyButton').disabled = false;
                        document.getElementById('verifyButton').innerHTML = 'Verify Payment';
                    }
                } catch (e) {
                    console.error('Error parsing response:', e);
                    alert('An error occurred during verification. Please try again.');
                }
            } else {
                alert('An error occurred during verification. Please try again.');
            }
            document.getElementById('verifyButton').disabled = false;
            document.getElementById('verifyButton').innerHTML = 'Verify Payment';
        }
    };
    
    // Disable verify button while processing
    document.getElementById('verifyButton').disabled = true;
    document.getElementById('verifyButton').innerHTML = 'Verifying...';
    
    xhr.open('POST', form.action, true);
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    xhr.send(formData);
    
    return false;
}