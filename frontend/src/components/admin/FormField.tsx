import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';

interface FormFieldProps {
  label: string;
  name: string;
  value: string | number | undefined;
  onChange: (name: string, value: string) => void;
  required?: boolean;
  type?: 'text' | 'number' | 'date' | 'email' | 'tel';
  placeholder?: string;
  textarea?: boolean;
  className?: string;
  disabled?: boolean;
}

export function FormField({
  label,
  name,
  value,
  onChange,
  required,
  type = 'text',
  placeholder,
  textarea,
  className,
  disabled,
}: FormFieldProps) {
  const id = `field-${name}`;
  const Comp = textarea ? Textarea : Input;

  return (
    <div className={cn('space-y-1.5', className)}>
      <Label htmlFor={id} className="text-xs font-medium">
        {label}
        {required && <span className="text-red-400 ml-0.5">*</span>}
      </Label>
      <Comp
        id={id}
        type={textarea ? undefined : type}
        value={value ?? ''}
        onChange={(e) => onChange(name, e.target.value)}
        placeholder={placeholder}
        required={required}
        disabled={disabled}
        className="h-8 text-sm"
      />
    </div>
  );
}
