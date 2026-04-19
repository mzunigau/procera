import type { ReactNode } from "react";

type Column<T> = {
  header: string;
  render: (item: T) => ReactNode;
};

type DataTableProps<T> = {
  columns: Array<Column<T>>;
  emptyMessage: string;
  items: T[];
};

export function DataTable<T>({ columns, emptyMessage, items }: DataTableProps<T>) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.header}>{column.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.length === 0 ? (
            <tr>
              <td className="empty-cell" colSpan={columns.length}>
                {emptyMessage}
              </td>
            </tr>
          ) : (
            items.map((item, index) => (
              <tr key={index}>
                {columns.map((column) => (
                  <td key={column.header}>{column.render(item)}</td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
