import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { SERVICE_TYPES } from '@/lib/constants';

interface Props {
  serviceType: string;
  monthsSinceService: number;
  startedBy: string;
  onServiceTypeChange: (v: string) => void;
  onMonthsChange: (v: number) => void;
  onStartedByChange: (v: string) => void;
}

export function StepServiceConfig({
  serviceType, monthsSinceService, startedBy,
  onServiceTypeChange, onMonthsChange, onStartedByChange,
}: Props) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">Configure the service parameters.</p>
      <Card>
        <CardHeader className="py-3 px-4">
          <CardTitle className="text-sm">Service Configuration</CardTitle>
        </CardHeader>
        <CardContent className="px-4 pb-4 space-y-4">
          <div className="space-y-2">
            <Label>Service Type</Label>
            <Select value={serviceType} onValueChange={onServiceTypeChange}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SERVICE_TYPES.map(st => (
                  <SelectItem key={st.value} value={st.value}>{st.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Months Since Last Service</Label>
            <Input
              type="number"
              min={0}
              max={240}
              value={monthsSinceService}
              onChange={e => onMonthsChange(Number(e.target.value))}
            />
            <p className="text-xs text-muted-foreground">
              Affects procedure — batteries {">"} 24 months may require extended rest periods.
            </p>
          </div>
          <div className="space-y-2">
            <Label>Technician Name</Label>
            <Input
              value={startedBy}
              onChange={e => onStartedByChange(e.target.value)}
              placeholder="Enter your name"
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
