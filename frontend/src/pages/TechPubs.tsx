import { PageHeader } from '@/components/common/PageHeader';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { useApiQuery } from '@/hooks/useApiQuery';
import { getTechPubs } from '@/api/techPubs';
import { Card } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

export default function TechPubs() {
  const { data, isLoading, error } = useApiQuery(() => getTechPubs(), []);

  return (
    <div>
      <PageHeader title="Tech Pubs" description="Component Maintenance Manuals" />
      {isLoading ? <LoadingSpinner /> : error ? (
        <p className="text-red-600">Failed to load tech pubs</p>
      ) : (
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>CMM Number</TableHead>
                <TableHead>Title</TableHead>
                <TableHead>Revision</TableHead>
                <TableHead>ATA Chapter</TableHead>
                <TableHead>Part Numbers</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data?.map(tp => (
                <TableRow key={tp.id}>
                  <TableCell className="font-mono">{tp.cmm_number}</TableCell>
                  <TableCell>{tp.title}</TableCell>
                  <TableCell>{tp.revision || '-'}</TableCell>
                  <TableCell>{tp.ata_chapter || '-'}</TableCell>
                  <TableCell className="text-xs font-mono">{tp.applicable_part_numbers?.join(', ')}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}
    </div>
  );
}
