import React from 'react';
import { Controller, Control, FieldValues, Path } from 'react-hook-form';

interface Option {
  label: string;
  value: string;
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
  return (
    <div style={styles.fieldContainer}>
      <label style={styles.label}>
        {label}
        {required && <span style={styles.required}>*</span>}
      </label>
      <Controller
        name={name}
        control={control}
        render={({ field }) => {
          if (type === 'textarea') {
            return <textarea {...field} style={styles.textarea} placeholder={placeholder} rows={rows ?? 3} />;
          }
          if (type === 'select') {
            return (
              <select {...field} style={styles.select} value={field.value ?? ''}>
                <option value="" disabled>{placeholder ?? `Select ${label.toLowerCase()}`}</option>
                {options?.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            );
          }
          if (type === 'checkbox-group') {
            return (
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
            );
          }
          return <input {...field} style={styles.input} placeholder={placeholder} />;
        }}
      />
      {error && <span style={styles.error}>{error}</span>}
    </div>
  );
}

export default FormField;
