let selectedService = null;
let selectedDate = null;
let selectedTime = null;
let services = [];

$(document).ready(function () {
    // Set minimum date to today
    const today = new Date().toISOString().split('T')[0];
    $('#appointmentDate').attr('min', today);

    // Load services from Flask API
    loadServices();
    setupEventListeners();
});

// Load services from /api/services
function loadServices() {
    $.get('/api/services', function (data) {
        services = data;
        displayServices(data);
    });
}

// Display service cards dynamically
function displayServices(services) {
    const html = services
        .map(
            (service) => `
        <div class="card service-card border-2 mb-3" data-id="${service.id}">
            <div class="card-body">
                <div class="row align-items-center">
                    <div class="col-auto">
                        <i class="fas fa-briefcase-medical text-primary" style="font-size: 2rem;"></i>
                    </div>
                    <div class="col">
                        <h5 class="mb-1">${service.name}</h5>
                        <small class="text-muted">
                            <i class="fas fa-clock"></i> ${service.duration} min | 
                            <i class="fas fa-dollar-sign"></i> $${service.price}
                        </small>
                    </div>
                </div>
            </div>
        </div>
    `
        )
        .join('');
    $('#servicesList').html(html);
}

// Set up all event listeners
function setupEventListeners() {
    // Step 1: Select service
    $(document).on('click', '.service-card', function () {
        $('.service-card').removeClass('selected');
        $(this).addClass('selected');
        selectedService = services.find(
            (s) => s.id == $(this).data('id')
        );
        $('#nextToStep2').prop('disabled', false);
    });

    // Step navigation
    $('#nextToStep2').click(() => goToStep(2));
    $('#backToStep1').click(() => goToStep(1));
    $('#nextToStep3').click(() => goToStep(3));
    $('#backToStep2').click(() => goToStep(2));
    $('#nextToStep4').click(() => goToStep(4));
    $('#backToStep3').click(() => goToStep(3));

    // Date selection
    $('#appointmentDate').change(function () {
        selectedDate = $(this).val();
        if (selectedDate) loadTimeSlots();
    });

    // Time slot selection (delegated)
    $(document).on('click', '.time-slot', function () {
        $('.time-slot').removeClass('selected');
        $(this).addClass('selected');
        selectedTime = $(this).data('time');
        $('#nextToStep3').prop('disabled', false);
    });

    // Confirm booking
    $('#confirmBooking').click(bookAppointment);
}

// Navigate between steps
function goToStep(step) {
    $('.form-step').removeClass('active');
    $(`#step${step}`).addClass('active');

    for (let i = 1; i <= 4; i++) {
        if (i < step) {
            $(`#step${i}-circle`)
                .removeClass('bg-secondary bg-primary')
                .addClass('bg-success');
            $(`#step${i}-label`)
                .removeClass('text-muted')
                .addClass('text-success');
        } else if (i === step) {
            $(`#step${i}-circle`)
                .removeClass('bg-secondary bg-success')
                .addClass('bg-primary');
            $(`#step${i}-label`)
                .removeClass('text-muted text-success')
                .addClass('fw-semibold text-primary');
        } else {
            $(`#step${i}-circle`)
                .removeClass('bg-primary bg-success')
                .addClass('bg-secondary');
            $(`#step${i}-label`)
                .removeClass('fw-semibold text-primary text-success')
                .addClass('text-muted');
        }
    }

    if (step === 4) showSummary();
}

// Load available time slots from Flask API
function loadTimeSlots() {
    $.ajax({
        url: '/api/available-slots',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            date: selectedDate,
            service_id: selectedService.id,
        }),
        success: function (slots) {
            if (slots.length === 0) {
                $('#timeSlotsContainer').html(
                    '<div class="alert alert-warning">No available slots for this date.</div>'
                );
            } else {
                const html =
                    '<label class="form-label fw-semibold">Select Time</label><div class="row g-2">' +
                    slots
                        .map(
                            (slot) => `
                    <div class="col-6 col-md-3">
                        <div class="time-slot card text-center p-2 border-2" data-time="${slot}">
                            <i class="fas fa-clock"></i> ${slot}
                        </div>
                    </div>
                `
                        )
                        .join('') +
                    '</div>';
                $('#timeSlotsContainer').html(html);
            }
        },
    });
}

// Show appointment summary before confirmation
function showSummary() {
    const html = `
        <div class="row g-3">
            <div class="col-md-6"><strong>Service:</strong></div>
            <div class="col-md-6">${selectedService.name}</div>
            <div class="col-md-6"><strong>Date:</strong></div>
            <div class="col-md-6"><i class="fas fa-calendar"></i> ${selectedDate}</div>
            <div class="col-md-6"><strong>Time:</strong></div>
            <div class="col-md-6"><i class="fas fa-clock"></i> ${selectedTime}</div>
            <div class="col-md-6"><strong>Duration:</strong></div>
            <div class="col-md-6">${selectedService.duration} minutes</div>
            <div class="col-md-6"><strong>Price:</strong></div>
            <div class="col-md-6 text-success fw-bold">$${selectedService.price}</div>
            <div class="col-md-6"><strong>Name:</strong></div>
            <div class="col-md-6">${$('#userName').val()}</div>
            <div class="col-md-6"><strong>Email:</strong></div>
            <div class="col-md-6">${$('#userEmail').val()}</div>
            <div class="col-md-6"><strong>Phone:</strong></div>
            <div class="col-md-6">${$('#userPhone').val()}</div>
        </div>
    `;
    $('#summaryContent').html(html);
}

// Book appointment via Flask API
function bookAppointment() {
    const data = {
        name: $('#userName').val(),
        email: $('#userEmail').val(),
        phone: $('#userPhone').val(),
        service_id: selectedService?.id,
        date: selectedDate,
        time: selectedTime,
        notes: $('#userNotes').val(),
    };

    if (!data.service_id || !data.date || !data.time) {
        alert('Please select a service, date, and time before confirming.');
        return;
    }

    $.ajax({
        url: '/api/book',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: function (response) {
            $('#confirmationDetails').html(`
                <strong>Appointment ID:</strong> #${response.appointment_id}<br>
                <strong>Service:</strong> ${selectedService.name}<br>
                <strong>Date & Time:</strong> ${selectedDate} at ${selectedTime}
            `);
            $('.form-step').removeClass('active');
            $('#successStep').addClass('active');
        },
        error: function (xhr) {
            alert('Error booking appointment: ' + xhr.responseText);
        },
    });
}
