// Handle Sign In
function handleSignIn(event) {
    event.preventDefault();
    
    const role = document.getElementById('signInRole').value;
    const email = document.getElementById('signInEmail').value.trim();
    const password = document.getElementById('signInPassword').value.trim();
    const adminKey = role === 'admin' ? document.getElementById('signInAdminKey').value.trim() : '';
    
    const data = { email, password, role };
    if (role === 'admin') {
        data.admin_key = adminKey;
    }
    
    fetch('/signin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            alert(result.message);
            window.location.href = result.redirect_url;
        } else {
            alert(result.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred. Please try again later.');
    });
}

// Handle Sign Up
function handleSignUp(event) {
    event.preventDefault();

    // Validate passwords match
    const password = document.getElementById('signUpPassword').value;
    const confirmPassword = document.getElementById('signUpConfirmPassword').value;

    if (password !== confirmPassword) {
        alert('Passwords do not match!');
        return;
    }

    const signUpForm = document.getElementById('signUpFormElement');
    const formData = new FormData(signUpForm);

    fetch('/register', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'OTP sent') {
            showOTPModal();
        } else {
            alert(data.status);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Show OTP Modal
function showOTPModal() {
    const modal = new bootstrap.Modal(document.getElementById('otpModal'));
    modal.show();
}

// Verify OTP
function verifyOTP() {
    const otp = document.getElementById('otpInput').value;
    const email = document.getElementById('signUpEmail').value;

    const formData = new FormData();
    formData.append('email', email);
    formData.append('otp', otp);

    fetch('/verify_otp', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json(),console.log(response))
    .then(data => {
        if (data.status === 'Email verified successfully!') {
            alert('Verification successful!');
            window.location.href = '/';  
        } else {
            alert(data.status);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}