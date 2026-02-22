import { PageHeader } from '@/components/common/PageHeader';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { useApiQuery } from '@/hooks/useApiQuery';
import { getBatteryProfiles } from '@/api/batteryProfiles';
import { Card } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

export default function BatteryProfiles() {
  const { data, isLoading, error } = useApiQuery(() => getBatteryProfiles(), []);

  return (
    <div>
      <PageHeader title="Battery Profiles" description="Battery type configurations and test parameters" />
      {isLoading ? <LoadingSpinner /> : error ? (
        <p className="text-red-600">Failed to load battery profiles</p>
      ) : (
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Part Number</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Chemistry</TableHead>
                <TableHead>Voltage</TableHead>
                <TableHead>Capacity</TableHead>
                <TableHead>Cells</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data?.map(p => (
                <TableRow key={p.id}>
                  <TableCell className="font-mono">{p.part_number}</TableCell>
                  <TableCell>{p.description}</TableCell>
                  <TableCell>{p.chemistry}</TableCell>
                  <TableCell>{p.nominal_voltage_v} V</TableCell>
                  <TableCell>{p.capacity_ah} Ah</TableCell>
                  <TableCell>{p.num_cells}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}
    </div>
  );
}
