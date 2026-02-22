import { PageHeader } from '@/components/common/PageHeader';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { useApiQuery } from '@/hooks/useApiQuery';
import { getRecipes } from '@/api/recipes';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

export default function Recipes() {
  const { data, isLoading, error } = useApiQuery(() => getRecipes(), []);

  return (
    <div>
      <PageHeader title="Recipes" description="Legacy test recipes (read-only, deprecated)" />
      <Badge variant="secondary" className="mb-4 bg-amber-600/20 text-amber-400 border-amber-600/30">
        Deprecated — Use Tech Pubs procedures for new jobs
      </Badge>
      {isLoading ? <LoadingSpinner /> : error ? (
        <p className="text-red-600">Failed to load recipes</p>
      ) : (
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>CMM Ref</TableHead>
                <TableHead>Part Number</TableHead>
                <TableHead>Steps</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data?.map(r => (
                <TableRow key={r.id}>
                  <TableCell className="font-medium">{r.name}</TableCell>
                  <TableCell className="font-mono text-muted-foreground">{r.cmm_ref || '-'}</TableCell>
                  <TableCell className="font-mono">{r.part_number || '-'}</TableCell>
                  <TableCell>{r.steps?.length ?? 0}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}
    </div>
  );
}
