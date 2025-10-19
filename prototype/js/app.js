// OCR Mate - Shared JavaScript Functionality

// Console welcome message
console.log('%c OCR Mate Prototype ', 'background: #3b82f6; color: white; font-size: 16px; padding: 5px 10px; border-radius: 5px;');
console.log('Inspired by LangStruct | Powered by DSPy GEPA');

// Utility Functions
const utils = {
  // Format currency
  formatCurrency: (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  },

  // Format date
  formatDate: (date) => {
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  },

  // Calculate confidence color
  getConfidenceColor: (confidence) => {
    if (confidence >= 90) return 'success';
    if (confidence >= 75) return 'warning';
    return 'danger';
  },

  // Show toast notification (simplified)
  toast: (message, type = 'info') => {
    alert(`[${type.toUpperCase()}] ${message}`);
  }
};

// Navigation highlighting
document.addEventListener('DOMContentLoaded', () => {
  const currentPath = window.location.pathname.split('/').pop() || 'index.html';
  const navLinks = document.querySelectorAll('.nav a');

  navLinks.forEach(link => {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
  });
});

// Add smooth scrolling
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      target.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
    }
  });
});

// Form validation helper
function validateForm(formId) {
  const form = document.getElementById(formId);
  if (!form) return false;

  const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
  let isValid = true;

  inputs.forEach(input => {
    if (!input.value.trim()) {
      input.style.borderColor = 'var(--danger-color)';
      isValid = false;
    } else {
      input.style.borderColor = 'var(--border-color)';
    }
  });

  return isValid;
}

// Export data functionality
function exportData(data, format) {
  switch(format) {
    case 'json':
      downloadFile(JSON.stringify(data, null, 2), 'extraction_results.json', 'application/json');
      break;
    case 'csv':
      const csv = convertToCSV(data);
      downloadFile(csv, 'extraction_results.csv', 'text/csv');
      break;
    default:
      utils.toast('Export format not supported yet', 'warning');
  }
}

function convertToCSV(data) {
  // Simplified CSV conversion
  const headers = Object.keys(data);
  const values = Object.values(data);
  return headers.join(',') + '\n' + values.join(',');
}

function downloadFile(content, filename, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

// Mock data for prototyping
const mockData = {
  documentTypes: [
    {
      id: 'dt_001',
      name: 'Invoice',
      description: 'Standard vendor invoices',
      fields: 15,
      accuracy: 95.3,
      documents: 834,
      model: 'gpt-4o',
      status: 'optimized'
    },
    {
      id: 'dt_002',
      name: 'Receipt',
      description: 'Expense receipts',
      fields: 8,
      accuracy: 89.7,
      documents: 312,
      model: 'claude-3.5',
      status: 'training'
    },
    {
      id: 'dt_003',
      name: 'W2 Tax Form',
      description: 'Employee tax forms',
      fields: 22,
      accuracy: 97.1,
      documents: 101,
      model: 'gemini-pro',
      status: 'optimized'
    }
  ],

  recentActivity: [
    { document: 'invoice_2024_001.pdf', type: 'Invoice', status: 'completed', accuracy: 98.2, time: '2 mins ago' },
    { document: 'receipt_starbucks.jpg', type: 'Receipt', status: 'review', accuracy: 76.4, time: '15 mins ago' },
    { document: 'w2_employee_smith.pdf', type: 'W2 Tax Form', status: 'completed', accuracy: 99.1, time: '1 hour ago' }
  ]
};

// Global functions for button actions
window.ocrMate = {
  utils,
  mockData,
  exportData,
  validateForm
};

console.log('OCR Mate prototype loaded successfully!');
