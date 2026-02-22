import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Search, Plus, MoreHorizontal, Pencil, Trash2 } from 'lucide-react';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';

export interface Column<T> {
  header: string;
  accessor: keyof T | ((row: T) => React.ReactNode);
  className?: string;
}

interface AdminCrudTableProps<T extends { id: number }> {
  title: string;
  data: T[] | null;
  columns: Column<T>[];
  isLoading: boolean;
  error: Error | null;
  onAdd?: () => void;
  onEdit: (item: T) => void;
  onDelete?: (item: T) => void;
  searchValue: string;
  onSearchChange: (value: string) => void;
  searchPlaceholder?: string;
}

export function AdminCrudTable<T extends { id: number }>({
  title,
  data,
  columns,
  isLoading,
  error,
  onAdd,
  onEdit,
  onDelete,
  searchValue,
  onSearchChange,
  searchPlaceholder = 'Search...',
}: AdminCrudTableProps<T>) {
  const [menuOpenId, setMenuOpenId] = useState<number | null>(null);

  const renderCell = (row: T, col: Column<T>) => {
    if (typeof col.accessor === 'function') return col.accessor(row);
    return String(row[col.accessor] ?? '-');
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold">{title}</h3>
        {onAdd && (
          <Button size="sm" onClick={onAdd}>
            <Plus className="h-3.5 w-3.5 mr-1" />
            Add
          </Button>
        )}
      </div>
      <div className="mb-3 relative max-w-xs">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
        <Input
          placeholder={searchPlaceholder}
          value={searchValue}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-8 h-8 text-sm"
        />
      </div>
      {isLoading ? (
        <LoadingSpinner />
      ) : error ? (
        <p className="text-red-600 text-sm">Failed to load {title.toLowerCase()}</p>
      ) : (
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                {columns.map((col) => (
                  <TableHead key={col.header} className={col.className}>
                    {col.header}
                  </TableHead>
                ))}
                <TableHead className="w-10" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {data?.map((row) => (
                <TableRow key={row.id}>
                  {columns.map((col) => (
                    <TableCell key={col.header} className={col.className}>
                      {renderCell(row, col)}
                    </TableCell>
                  ))}
                  <TableCell>
                    <DropdownMenu
                      open={menuOpenId === row.id}
                      onOpenChange={(open) =>
                        setMenuOpenId(open ? row.id : null)
                      }
                    >
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon-xs">
                          <MoreHorizontal className="h-3.5 w-3.5" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={() => {
                            setMenuOpenId(null);
                            onEdit(row);
                          }}
                        >
                          <Pencil className="h-3.5 w-3.5" />
                          Edit
                        </DropdownMenuItem>
                        {onDelete && (
                          <DropdownMenuItem
                            variant="destructive"
                            onClick={() => {
                              setMenuOpenId(null);
                              onDelete(row);
                            }}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                            Delete
                          </DropdownMenuItem>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
              {data?.length === 0 && (
                <TableRow>
                  <TableCell
                    colSpan={columns.length + 1}
                    className="text-center text-muted-foreground"
                  >
                    No {title.toLowerCase()} found
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </Card>
      )}
    </div>
  );
}
