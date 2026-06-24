import React from 'react';
import { Controller, Control, FieldValues, Path } from 'react-hook-form';

interface Option {
  label: string;
  value: string;
  disabled?: boolean;
}

interface FormFieldProps<T extends FieldValues> {
  name: Path<T>;
  control: Control<T>;
  label: string;
  type?: 'input' | 'textarea' | 'select' | 'checkbox-group';
  placeholder?: string;
  rows?: number;
  options?: Option[];
  error?: string;
  required?: boolean;
}

const styles = {
  fieldContainer: { marginBottom: '16px' } as React.CSSProperties,
  label: { display: 'block', marginBottom: '4px', fontWeight: 500, color: '#555' } as React.CSSProperties,
  input: {
    width: '100%', padding: '8px 12px', border: '1px solid #ccc',
    borderRadius: '4px', fontSize: '14px', boxSizing: 'border-box' as const,
  },
  textarea: {
    width: '100%', padding: '8px 12px', border: '1px solid #ccc',
    borderRadius: '4px', fontSize: '14px', boxSizing: 'border-box' as const,
    resize: 'vertical' as const,
  },
  select: {
    width: '100%', padding: '8px 12px', border: '1px solid #ccc',
    borderRadius: '4px', fontSize: '14px', boxSizing: 'border-box' as const,
    backgroundColor: '#fff',
  },
  checkboxGroup: { display: 'flex', flexDirection: 'column' as const, gap: '8px' },
  checkboxLabel: { display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' } as React.CSSProperties,
  checkboxText: { fontSize: '14px' },
  error: { color: '#f44336', fontSize: '12px', marginTop: '4px', display: 'block' } as React.CSSProperties,
  required: { color: '#f44336', marginLeft: '2px' },
};

function FormField<T extends FieldValues>({
  name, control, label, type = 'input', placeholder, rows,
  options, error, required,
}: FormFieldProps<T>) {
  const fieldId = `field-${name}`;
  const errorId = `error-${name}`;

  return (
    <div style={styles.fieldContainer}>
      <label htmlFor={fieldId} style={styles.label}>
        {label}
        {required && <span style={styles.required} aria-hidden="true">*</span>}
      </label>
      <Controller
        name={name}
        control={control}
        render={({ field }) => {
          const ariaProps = {
            id: fieldId,
            'aria-required': required || undefined,
            'aria-invalid': error ? true as const : undefined,
            'aria-describedby': error ? errorId : undefined,
          };
          if (type === 'textarea') {
            return <textarea {...field} {...ariaProps} style={styles.textarea} placeholder={placeholder} rows={rows ?? 3} />;
          }
          if (type === 'select') {
            return (
              <select {...field} {...ariaProps} style={styles.select} value={field.value ?? ''}>
                <option value="" disabled>{placeholder ?? `Select ${label.toLowerCase()}`}</option>
                {options?.map((opt) => (
                  <option key={opt.value} value={opt.value} disabled={opt.disabled}>
                    {opt.label}
                  </option>
                ))}
              </select>
            );
          }
          if (type === 'checkbox-group') {
            return (
              <fieldset style={{ border: 'none', padding: 0, margin: 0 }}>
                <legend style={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden', clip: 'rect(0,0,0,0)' }}>
                  {label}
                </legend>
                <div style={styles.checkboxGroup}>
                  {options?.map((opt) => (
                    <label key={opt.value} style={styles.checkboxLabel}>
                      <input
                        type="checkbox"
                        checked={(field.value as string[])?.includes(opt.value) ?? false}
                        onChange={(e) => {
                          const current = (field.value as string[]) || [];
                          field.onChange(
                            e.target.checked
                              ? [...current, opt.value]
                              : current.filter((v: string) => v !== opt.value)
                          );
                        }}
                      />
                      <span style={styles.checkboxText}>{opt.label}</span>
                    </label>
                  ))}
                </div>
              </fieldset>
            );
          }
          return <input {...field} {...ariaProps} style={styles.input} placeholder={placeholder} />;
        }}
      />
      {error && <span id={errorId} style={styles.error} role="alert">{error}</span>}
    </div>
  );
}

export default FormField;
