document.addEventListener('DOMContentLoaded', function () {
  const codeInput = document.getElementById('codeInput');
  const charCount = document.getElementById('charCount');
  const lineCount = document.getElementById('lineCount');
  const clearBtn = document.getElementById('clearBtn');
  const loadExampleBtn = document.getElementById('loadExampleBtn');
  const reviewForm = document.getElementById('reviewForm');
  const loadingOverlay = document.getElementById('loadingOverlay');
  const submitBtn = document.getElementById('submitBtn');
  const submitText = document.getElementById('submitText');

  const EXAMPLE_CODE = `import os
import json

def process_files(directory, extensions=['.py', '.js']):
    """Process files in a directory."""
    results = {}
    
    for filename in os.listdir(directory):
        name, ext = os.path.splitext(filename)
        if ext in extensions:
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                results[filename] = len(content.splitlines())
            except:
                pass
    
    return results

class FileAnalyzer:
    def __init__(self):
        self.cache = {}
    
    def analyze(self, path):
        global cache
        cache = self.process(path)
        return cache
    
    def process(self, path):
        data = process_files(path)
        return json.dumps(data)

analyzer = FileAnalyzer()
result = analyzer.analyze("/tmp")
print(result)`;

  function updateCounts() {
    if (!codeInput) return;
    const text = codeInput.value;
    charCount.textContent = text.length.toLocaleString() + ' chars';
    lineCount.textContent = text.split('\n').length.toLocaleString() + ' lines';
  }

  if (codeInput) {
    codeInput.addEventListener('input', updateCounts);
    updateCounts();

    codeInput.addEventListener('keydown', function (e) {
      if (e.key === 'Tab') {
        e.preventDefault();
        const start = this.selectionStart;
        const end = this.selectionEnd;
        this.value = this.value.substring(0, start) + '    ' + this.value.substring(end);
        this.selectionStart = this.selectionEnd = start + 4;
        updateCounts();
      }
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener('click', function () {
      if (codeInput) {
        codeInput.value = '';
        updateCounts();
        codeInput.focus();
      }
    });
  }

  if (loadExampleBtn) {
    loadExampleBtn.addEventListener('click', function () {
      if (codeInput) {
        codeInput.value = EXAMPLE_CODE;
        updateCounts();
        codeInput.focus();
      }
    });
  }

  if (reviewForm && loadingOverlay) {
    reviewForm.addEventListener('submit', function (e) {
      const code = codeInput ? codeInput.value.trim() : '';
      if (!code) return;

      loadingOverlay.classList.remove('hidden');
      if (submitBtn) submitBtn.disabled = true;
      if (submitText) submitText.textContent = 'Analyzing…';

      const steps = ['step1', 'step2', 'step3', 'step4'];
      let currentStep = 0;

      function activateNextStep() {
        if (currentStep > 0) {
          const prevStep = document.getElementById(steps[currentStep - 1]);
          if (prevStep) {
            prevStep.classList.remove('active');
            prevStep.classList.add('done');
          }
        }
        if (currentStep < steps.length) {
          const step = document.getElementById(steps[currentStep]);
          if (step) step.classList.add('active');
          currentStep++;
          if (currentStep < steps.length) {
            setTimeout(activateNextStep, 2500);
          }
        }
      }

      activateNextStep();
    });
  }
});
