import React, { useState, useEffect } from 'react';
import {
  setLLMConfig,
  getLLMConfig,
  resetLLMConfig,
  LLMConfigData,
  LLMValidationData,
} from '../../../api/llmConfigApi';

interface ModelConfigModalProps {
  visible: boolean;
  onClose: () => void;
  onConfigChanged: () => void;
}

const ModelConfigModal: React.FC<ModelConfigModalProps> = ({ visible, onClose, onConfigChanged }) => {
  const [modelName, setModelName] = useState('');
  const [thinkingEnabled, setThinkingEnabled] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [baseUrl, setBaseUrl] = useState('');

  const [currentConfig, setCurrentConfig] = useState<LLMConfigData | null>(null);
  const [validating, setValidating] = useState(false);
  const [applying, setApplying] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [validation, setValidation] = useState<LLMValidationData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (visible) {
      setError(null);
      setValidation(null);
      setFieldErrors({});
      fetchCurrentConfig();
    }
  }, [visible]);

  const fetchCurrentConfig = async () => {
    try {
      const response = await getLLMConfig();
      if (response.success) {
        setCurrentConfig(response.data);
        if (response.data.is_custom) {
          setModelName(response.data.model_name);
          setThinkingEnabled(response.data.thinking_enabled);
          setApiKey('');
          setBaseUrl(response.data.base_url || '');
        }
      }
    } catch {
      // Silently ignore — config fetch is best-effort for display
    }
  };

  const validateFields = (): boolean => {
    const errors: Record<string, string> = {};
    if (!modelName.trim()) {
      errors.modelName = 'Model name is required.';
    }
    if (!apiKey.trim()) {
      errors.apiKey = 'API key is required.';
    }
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleTestConnection = async () => {
    if (!validateFields()) return;

    setValidating(true);
    setError(null);
    setValidation(null);

    try {
      const response = await setLLMConfig({
        model_name: modelName.trim(),
        thinking_enabled: thinkingEnabled,
        api_key: apiKey.trim(),
        base_url: baseUrl.trim(),
      });

      const validationData = response.data?.validation;
      if (validationData) {
        setValidation(validationData);
      }

      if (response.success) {
        setCurrentConfig(response.data.config);
        onConfigChanged();
      } else {
        setError(response.message || 'Failed to validate configuration.');
      }
    } catch (err: any) {
      const msg =
        err.response?.data?.message ||
        err.message ||
        'Network error. Check that the backend is running.';
      setError(msg);
    } finally {
      setValidating(false);
    }
  };

  const handleApply = async () => {
    if (!validateFields()) return;
    if (!validation || !validation.valid) {
      // Must test connection first
      await handleTestConnection();
      return;
    }

    // Config is already saved by the validation endpoint, just close
    onConfigChanged();
    onClose();
  };

  const handleReset = async () => {
    setResetting(true);
    setError(null);
    try {
      const response = await resetLLMConfig();
      if (response.success) {
        setCurrentConfig(response.data);
        setModelName('');
        setThinkingEnabled(false);
        setApiKey('');
        setBaseUrl('');
        setValidation(null);
        onConfigChanged();
      } else {
        setError(response.message || 'Failed to reset configuration.');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to reset configuration.');
    } finally {
      setResetting(false);
    }
  };

  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!visible) return null;

  const isValidated = validation?.valid === true;

  return (
    <div style={s.overlay} onClick={handleOverlayClick} role="presentation">
      <div style={s.modal} role="dialog" aria-labelledby="model-config-title">
        <div style={s.header}>
          <h2 id="model-config-title" style={s.title}>Model Configuration</h2>
          <button style={s.closeButton} onClick={onClose} type="button" aria-label="Close">
            &times;
          </button>
        </div>

        <div style={s.body}>
          {currentConfig?.is_custom && (
            <div style={s.infoBanner}>
              Custom model active: <strong>{currentConfig.model_name}</strong>
              {currentConfig.thinking_enabled ? ' (thinking enabled)' : ''}
            </div>
          )}

          {!currentConfig?.is_custom && currentConfig && currentConfig.model_name && (
            <div style={s.infoBannerDefault}>
              Using server default: <strong>{currentConfig.model_name}</strong>
            </div>
          )}

          {!currentConfig?.is_custom && currentConfig && !currentConfig.model_name && (
            <div style={{ ...s.infoBannerDefault, backgroundColor: '#fff3e0', borderLeft: '4px solid #e65100' }}>
              No LLM model configured. Enter a model below to get started.
            </div>
          )}

          <div style={s.fieldGroup}>
            <label htmlFor="model-name-input" style={s.label}>Model Name <span style={s.required} aria-hidden="true">*</span></label>
            <input
              id="model-name-input"
              style={{
                ...s.input,
                ...(fieldErrors.modelName ? s.inputError : {}),
              }}
              type="text"
              value={modelName}
              onChange={(e) => {
                setModelName(e.target.value);
                setValidation(null);
                if (fieldErrors.modelName) setFieldErrors((p) => ({ ...p, modelName: '' }));
              }}
              placeholder="e.g., deepseek-v4-pro, gpt-4.1"
              disabled={applying}
              aria-required="true"
              aria-invalid={!!fieldErrors.modelName}
              aria-describedby={fieldErrors.modelName ? 'error-modelName' : undefined}
            />
            {fieldErrors.modelName && <div id="error-modelName" style={s.fieldError} role="alert">{fieldErrors.modelName}</div>}
          </div>

          <div style={s.fieldGroup}>
            <label htmlFor="api-key-input" style={s.label}>API Key <span style={s.required} aria-hidden="true">*</span></label>
            <input
              id="api-key-input"
              style={{
                ...s.input,
                ...(fieldErrors.apiKey ? s.inputError : {}),
              }}
              type="password"
              value={apiKey}
              onChange={(e) => {
                setApiKey(e.target.value);
                setValidation(null);
                if (fieldErrors.apiKey) setFieldErrors((p) => ({ ...p, apiKey: '' }));
              }}
              placeholder="Enter your API key"
              disabled={applying}
              aria-required="true"
              aria-invalid={!!fieldErrors.apiKey}
              aria-describedby={fieldErrors.apiKey ? 'error-apiKey' : undefined}
            />
            {fieldErrors.apiKey && <div id="error-apiKey" style={s.fieldError} role="alert">{fieldErrors.apiKey}</div>}
          </div>

          <div style={s.fieldGroup}>
            <label htmlFor="base-url-input" style={s.label}>Base URL <span style={s.hint}>(optional — auto-detected if empty)</span></label>
            <input
              id="base-url-input"
              style={s.input}
              type="text"
              value={baseUrl}
              onChange={(e) => {
                setBaseUrl(e.target.value);
                setValidation(null);
              }}
              placeholder="e.g., https://api.deepseek.com"
              disabled={applying}
            />
          </div>

          <div style={s.fieldGroup}>
            <label style={s.checkboxLabel}>
              <input
                type="checkbox"
                checked={thinkingEnabled}
                onChange={(e) => {
                  setThinkingEnabled(e.target.checked);
                  setValidation(null);
                }}
                disabled={applying}
                style={s.checkbox}
              />
              Enable Thinking / Reasoning Mode
            </label>
          </div>

          {validation && (
            <div style={{
              ...s.validationBox,
              backgroundColor: validation.valid ? '#e8f5e9' : '#ffebee',
              borderColor: validation.valid ? '#4caf50' : '#f44336',
            }}>
              <div style={{
                ...s.validationTitle,
                color: validation.valid ? '#2e7d32' : '#c62828',
              }}>
                {validation.valid ? '✓ Connection Verified' : '✗ Connection Failed'}
              </div>
              <div style={s.validationMsg}>{validation.message}</div>
              {validation.latency_ms > 0 && (
                <div style={s.validationMeta}>
                  Latency: {validation.latency_ms.toFixed(0)}ms
                  {validation.tokens_used > 0 && ` · Tokens: ${validation.tokens_used}`}
                </div>
              )}
            </div>
          )}

          {error && (
            <div style={s.errorBox}>
              <strong>Error:</strong> {error}
            </div>
          )}
        </div>

        <div style={s.footer}>
          <div style={s.footerLeft}>
            {currentConfig?.is_custom && (
              <button
                type="button"
                onClick={handleReset}
                disabled={resetting || applying || validating}
                style={s.resetButton}
              >
                {resetting ? 'Resetting...' : 'Reset to Default'}
              </button>
            )}
          </div>
          <div style={s.footerRight}>
            <button
              type="button"
              onClick={onClose}
              disabled={applying || validating}
              style={s.cancelButton}
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleTestConnection}
              disabled={validating || applying}
              style={{
                ...s.testButton,
                opacity: validating || applying ? 0.6 : 1,
                cursor: validating || applying ? 'not-allowed' : 'pointer',
              }}
            >
              {validating ? 'Testing...' : 'Test & Save'}
            </button>
            {isValidated && (
              <button
                type="button"
                onClick={handleApply}
                style={s.applyButton}
              >
                Apply
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const s: Record<string, React.CSSProperties> = {
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 10000,
  },
  modal: {
    backgroundColor: '#fff',
    borderRadius: '8px',
    width: '520px',
    maxWidth: '95vw',
    maxHeight: '85vh',
    overflowY: 'auto',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.25)',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '16px 20px',
    borderBottom: '1px solid #e0e0e0',
  },
  title: {
    margin: 0,
    fontSize: '18px',
    fontWeight: 600,
    color: '#333',
  },
  closeButton: {
    border: 'none',
    backgroundColor: 'transparent',
    fontSize: '24px',
    cursor: 'pointer',
    color: '#888',
    padding: '0 4px',
    lineHeight: 1,
  },
  body: {
    padding: '20px',
  },
  infoBanner: {
    padding: '10px 12px',
    backgroundColor: '#e3f2fd',
    border: '1px solid #90caf9',
    borderRadius: '4px',
    fontSize: '13px',
    color: '#1565c0',
    marginBottom: '16px',
  },
  infoBannerDefault: {
    padding: '10px 12px',
    backgroundColor: '#f5f5f5',
    border: '1px solid #e0e0e0',
    borderRadius: '4px',
    fontSize: '13px',
    color: '#666',
    marginBottom: '16px',
  },
  fieldGroup: {
    marginBottom: '16px',
  },
  label: {
    display: 'block',
    fontSize: '13px',
    fontWeight: 600,
    color: '#555',
    marginBottom: '6px',
  },
  required: {
    color: '#f44336',
  },
  hint: {
    fontWeight: 400,
    color: '#999',
    fontSize: '12px',
  },
  input: {
    width: '100%',
    padding: '8px 12px',
    border: '1px solid #ccc',
    borderRadius: '4px',
    fontSize: '14px',
    boxSizing: 'border-box',
    outline: 'none',
  },
  inputError: {
    borderColor: '#f44336',
    backgroundColor: '#fff5f5',
  },
  fieldError: {
    fontSize: '12px',
    color: '#f44336',
    marginTop: '4px',
  },
  checkboxLabel: {
    display: 'flex',
    alignItems: 'center',
    fontSize: '14px',
    color: '#333',
    cursor: 'pointer',
  },
  checkbox: {
    marginRight: '8px',
    width: '16px',
    height: '16px',
    cursor: 'pointer',
  },
  validationBox: {
    padding: '12px',
    borderRadius: '4px',
    border: '1px solid',
    marginBottom: '12px',
  },
  validationTitle: {
    fontSize: '14px',
    fontWeight: 600,
    marginBottom: '4px',
  },
  validationMsg: {
    fontSize: '13px',
    color: '#555',
    marginBottom: '4px',
  },
  validationMeta: {
    fontSize: '12px',
    color: '#888',
  },
  errorBox: {
    padding: '12px',
    backgroundColor: '#ffebee',
    border: '1px solid #f44336',
    borderRadius: '4px',
    color: '#c62828',
    fontSize: '13px',
    marginBottom: '12px',
    whiteSpace: 'pre-wrap',
  },
  footer: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px 20px',
    borderTop: '1px solid #e0e0e0',
  },
  footerLeft: {},
  footerRight: {
    display: 'flex',
    gap: '8px',
    marginLeft: 'auto',
  },
  cancelButton: {
    padding: '8px 20px',
    backgroundColor: '#fff',
    color: '#555',
    border: '1px solid #ccc',
    borderRadius: '4px',
    fontSize: '14px',
    cursor: 'pointer',
    fontWeight: 500,
  },
  testButton: {
    padding: '8px 20px',
    backgroundColor: '#1565c0',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    fontSize: '14px',
    fontWeight: 600,
    cursor: 'pointer',
  },
  applyButton: {
    padding: '8px 20px',
    backgroundColor: '#4caf50',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    fontSize: '14px',
    fontWeight: 600,
    cursor: 'pointer',
  },
  resetButton: {
    padding: '8px 16px',
    backgroundColor: '#fff',
    color: '#c62828',
    border: '1px solid #c62828',
    borderRadius: '4px',
    fontSize: '13px',
    cursor: 'pointer',
  },
};

export default ModelConfigModal;
