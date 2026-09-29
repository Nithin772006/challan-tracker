/**
 * Smart Traffic Violation Logger
 * Frontend Interactions & UX Enhancements
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Navigation Toggle
  const mobileToggle = document.getElementById('mobileNavToggle');
  const navLinks = document.getElementById('navLinks');
  if (mobileToggle && navLinks) {
    mobileToggle.addEventListener('click', () => {
      navLinks.classList.toggle('is-active');
    });
  }

  // 2. Dismissible Toasts
  const toasts = document.querySelectorAll('.toast');
  toasts.forEach((toast) => {
    // Auto fadeout after 5 seconds
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 250);
    }, 5000);

    const closeBtn = toast.querySelector('.toast-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 250);
      });
    }
  });

  // 3. Vehicle Number Auto-Uppercase on typing
  const vehicleInputs = document.querySelectorAll('input[name="vehicle_number"]');
  vehicleInputs.forEach((input) => {
    input.addEventListener('input', (e) => {
      const start = e.target.selectionStart;
      const end = e.target.selectionEnd;
      e.target.value = e.target.value.toUpperCase().replace(/\s+/g, '');
      e.target.setSelectionRange(start, end);
    });
  });

  // 4. Auto Fine Amount Suggestion when selecting Violation Type
  const violationTypeSelect = document.getElementById('violation_type');
  const fineAmountInput = document.getElementById('fine_amount');
  
  const fineSuggestionMap = {
    'No Helmet': 1000,
    'Overspeeding': 2000,
    'Signal Jump': 1000,
    'No Seat Belt': 1000,
    'Drunk Driving': 10000,
    'Wrong Parking': 500,
    'Driving Without License': 5000,
    'Triple Riding': 1000,
    'Mobile Phone While Driving': 1500,
    'Other': 1000
  };

  if (violationTypeSelect && fineAmountInput) {
    violationTypeSelect.addEventListener('change', () => {
      const selectedType = violationTypeSelect.value;
      if (fineSuggestionMap[selectedType] && (!fineAmountInput.value || fineAmountInput.dataset.touched !== 'true')) {
        fineAmountInput.value = fineSuggestionMap[selectedType];
      }
    });

    fineAmountInput.addEventListener('input', () => {
      fineAmountInput.dataset.touched = 'true';
    });
  }

  // 5. Delete Confirmation Modal
  const deleteModal = document.getElementById('deleteModal');
  const deleteForm = document.getElementById('deleteViolationForm');
  const deleteChallanSpan = document.getElementById('deleteChallanNumber');
  const deleteBtns = document.querySelectorAll('.js-delete-violation');
  const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');

  if (deleteModal && deleteForm) {
    deleteBtns.forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const violationId = btn.getAttribute('data-id');
        const challanNumber = btn.getAttribute('data-challan');
        deleteForm.action = `/violations/${violationId}/delete`;
        if (deleteChallanSpan) {
          deleteChallanSpan.textContent = challanNumber;
        }
        deleteModal.classList.add('is-open');
      });
    });

    if (cancelDeleteBtn) {
      cancelDeleteBtn.addEventListener('click', () => {
        deleteModal.classList.remove('is-open');
      });
    }

    deleteModal.addEventListener('click', (e) => {
      if (e.target === deleteModal) {
        deleteModal.classList.remove('is-open');
      }
    });
  }

  // 6. Quick Print helper
  const printBtns = document.querySelectorAll('.js-print-trigger');
  printBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      window.print();
    });
  });
});
