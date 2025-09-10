import { useState, useEffect, useMemo } from 'react';
import { DataTable } from 'mantine-datatable';
import Papa from 'papaparse';
import {
  Box,
  TextInput,
  Group,
  Button,
  Popover,
  Stack,
  Checkbox,
  Text,
  ActionIcon,
  Anchor,
} from '@mantine/core';
import { IconFilter, IconSettings, IconCheck, IconEdit, IconX } from '@tabler/icons-react';
import { DndContext, closestCenter } from '@dnd-kit/core';
import {
  SortableContext,
  horizontalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
// Types for CSV data format
interface MetricData {
  metric_name: string;
  metric: string | boolean;
  details: string;
  citations: string[];
}

interface CompanyCSV {
  "Company Name": string;
  "State": string;
  "Investment Grade": string;
  "Metrics": string; // JSON string
  "Website"?: string;
  "Contact Info"?: string;
  "annual_average_employees_2020"?: string;
  "annual_average_employees_2021"?: string;
  "annual_average_employees_2022"?: string;
  "annual_average_employees_2023"?: string;
  "annual_average_employees_2024"?: string;
  "total_hours_worked_2020"?: string;
  "total_hours_worked_2021"?: string;
  "total_hours_worked_2022"?: string;
  "total_hours_worked_2023"?: string;
  "total_hours_worked_2024"?: string;
}

interface Company {
  company_name: string;
  state: string;
  investment_grade: string;
  investment_grade_summary: string;
  investment_grade_citations: string[];
  est_annual_revenue: string;
  est_annual_revenue_citations: string[];
  est_yoy_growth: string;
  est_yoy_growth_citations: string[];
  pe_backed: string;
  pe_backed_citations: string[];
  can_accommodate_allocation: string;
  can_accommodate_allocation_citations: string[];
  good_reputation: string;
  good_reputation_citations: string[];
  website?: string;
  contact_info?: string;
  annual_average_employees_2020?: string;
  annual_average_employees_2021?: string;
  annual_average_employees_2022?: string;
  annual_average_employees_2023?: string;
  annual_average_employees_2024?: string;
  total_hours_worked_2020?: string;
  total_hours_worked_2021?: string;
  total_hours_worked_2022?: string;
  total_hours_worked_2023?: string;
  total_hours_worked_2024?: string;
}

interface ColumnConfig {
  key: keyof Company;
  label: string;
  type: 'definition' | 'metric';
  visible: boolean;
  order: number;
  group?: string;
}

interface DataTableColumn<T> {
  accessor: keyof T;
  title?: React.ReactNode;
  render?: (record: T) => React.ReactNode;
  sortable?: boolean;
}

interface DragEndEvent {
  active: { id: string | number };
  over: { id: string | number } | null;
}

const columnConfigs: ColumnConfig[] = [
  { key: 'company_name', label: 'Company Name', type: 'definition', visible: true, order: 0 },
  { key: 'state', label: 'State', type: 'definition', visible: true, order: 1 },
  { key: 'investment_grade', label: 'Investment Grade', type: 'metric', visible: true, order: 2 },
  { key: 'est_annual_revenue', label: 'Est. Annual Rev. ($)', type: 'metric', visible: true, order: 3 },
  { key: 'est_yoy_growth', label: 'Est. YoY Growth (%)', type: 'metric', visible: true, order: 4 },
  { key: 'pe_backed', label: 'PE-backed (y/n)', type: 'metric', visible: true, order: 5 },
  { key: 'can_accommodate_allocation', label: 'Can Accommodate $10M', type: 'metric', visible: true, order: 6 },
  { key: 'annual_average_employees_2020', label: '2020', type: 'metric', visible: true, order: 7, group: 'Avg Employees (OSHA)' },
  { key: 'annual_average_employees_2021', label: '2021', type: 'metric', visible: true, order: 8, group: 'Avg Employees (OSHA)' },
  { key: 'annual_average_employees_2022', label: '2022', type: 'metric', visible: true, order: 9, group: 'Avg Employees (OSHA)' },
  { key: 'annual_average_employees_2023', label: '2023', type: 'metric', visible: true, order: 10, group: 'Avg Employees (OSHA)' },
  { key: 'annual_average_employees_2024', label: '2024', type: 'metric', visible: true, order: 11, group: 'Avg Employees (OSHA)' },
  { key: 'total_hours_worked_2020', label: '2020', type: 'metric', visible: true, order: 12, group: 'Total Hours Worked (OSHA)' },
  { key: 'total_hours_worked_2021', label: '2021', type: 'metric', visible: true, order: 13, group: 'Total Hours Worked (OSHA)' },
  { key: 'total_hours_worked_2022', label: '2022', type: 'metric', visible: true, order: 14, group: 'Total Hours Worked (OSHA)' },
  { key: 'total_hours_worked_2023', label: '2023', type: 'metric', visible: true, order: 15, group: 'Total Hours Worked (OSHA)' },
  { key: 'total_hours_worked_2024', label: '2024', type: 'metric', visible: true, order: 16, group: 'Total Hours Worked (OSHA)' },
];


interface SortableHeaderProps {
  children: React.ReactNode;
  id: string;
}

function SortableHeader({ children, id }: SortableHeaderProps) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      {children}
    </div>
  );
}

interface MetricCellProps {
  value: string;
  citations: string[];
  companyName: string;
  metricKey: string;
  onVerificationChange: (companyName: string, metricKey: string, verified: boolean) => void;
  isVerified: boolean;
  onValueChange: (companyName: string, metricKey: string, newValue: string) => void;
  originalValue: string;
  isEdited: boolean;
  onRevert: (companyName: string, metricKey: string) => void;
}

function MetricCell({ value, citations, companyName, metricKey, onVerificationChange, isVerified, onValueChange, originalValue: _originalValue, isEdited, onRevert }: MetricCellProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value);
  const [popoverOpened, setPopoverOpened] = useState(false);
  const [_closeTimeout, _setCloseTimeout] = useState<NodeJS.Timeout | null>(null);

  const handleVerificationToggle = () => {
    onVerificationChange(companyName, metricKey, !isVerified);
  };

  const handleEditStart = () => {
    setEditValue(value);
    setIsEditing(true);
  };

  const handleEditSave = () => {
    onValueChange(companyName, metricKey, editValue);
    setIsEditing(false);
  };

  const handleEditCancel = () => {
    setEditValue(value);
    setIsEditing(false);
  };

  const handleRevert = () => {
    onRevert(companyName, metricKey);
  };

  const tooltipContent = citations && citations.length > 0 ? (
    <Stack gap="xs">
      <Text size="sm" fw={600}>Citations:</Text>
      {citations.map((url, index) => (
        <Anchor
          key={index}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          size="sm"
          c="blue"
          style={{
            wordBreak: 'break-all',
            whiteSpace: 'normal',
            lineHeight: 1.4,
            display: 'block',
            maxWidth: '100%',
            overflow: 'hidden',
            textOverflow: 'ellipsis'
          }}
        >
          [{index + 1}] {url}
        </Anchor>
      ))}
    </Stack>
  ) : (
    <Text size="sm" c="gray.6">
      No citations available
    </Text>
  );

  if (isEditing) {
    return (
      <Group gap={4} wrap="nowrap">
        <TextInput
          value={editValue}
          onChange={(e) => setEditValue(e.currentTarget.value)}
          size="xs"
          style={{ minWidth: 100 }}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleEditSave();
            if (e.key === 'Escape') handleEditCancel();
          }}
          autoFocus
        />
        <ActionIcon 
          size="sm"
          variant="filled"
          className="action-btn-save"
          style={{
            width: '24px',
            height: '24px',
            minWidth: '24px',
            minHeight: '24px'
          }}
          onClick={handleEditSave}
        >
          <IconCheck size={12} />
        </ActionIcon>
        <ActionIcon 
          size="sm"
          variant="filled" 
          className="action-btn-cancel"
          style={{
            width: '24px',
            height: '24px',
            minWidth: '24px',
            minHeight: '24px'
          }}
          onClick={handleEditCancel}
        >
          <IconX size={12} />
        </ActionIcon>
      </Group>
    );
  }

  const metricElement = (
    <Popover
      width={450}
      position="top"
      withArrow
      shadow="md"
      opened={popoverOpened}
      onChange={setPopoverOpened}
    >
      <Popover.Target>
        <div 
          style={{ 
            position: 'relative', 
            width: '100%',
            minHeight: '40px',
            display: 'flex',
            alignItems: 'center',
            backgroundColor: isEdited ? 'var(--eanna-accent-gold)' : 'transparent',
            cursor: 'pointer',
            padding: '8px 12px',
            margin: '-8px -12px',
            borderRadius: '6px',
            border: '1px solid transparent',
            transition: 'all 0.2s ease'
          }}
          onClick={() => setPopoverOpened(!popoverOpened)}
          onMouseEnter={(e) => {
            if (!isEdited) {
              e.target.style.backgroundColor = 'var(--eanna-light-blue)';
              e.target.style.borderColor = 'var(--eanna-electric-blue)';
            }
          }}
          onMouseLeave={(e) => {
            if (!isEdited) {
              e.target.style.backgroundColor = 'transparent';
              e.target.style.borderColor = 'transparent';
            }
          }}
        >
          <Text 
            size="sm"
            style={{
              color: 'var(--eanna-gray-800)',
              fontWeight: 500,
              fontFamily: 'var(--eanna-font-sans)'
            }}
          >
            {value}
          </Text>
        </div>
      </Popover.Target>
      <Popover.Dropdown>
        {tooltipContent}
      </Popover.Dropdown>
    </Popover>
  );

  return (
    <Group gap={4} wrap="nowrap">
      {metricElement}
      <ActionIcon
        size="sm"
        variant="filled"
        onClick={handleEditStart}
        className="action-btn-edit"
        style={{ 
          flexShrink: 0,
          width: '24px',
          height: '24px',
          minWidth: '24px',
          minHeight: '24px'
        }}
      >
        <IconEdit size={12} />
      </ActionIcon>
      {isEdited && (
        <ActionIcon
          size="sm"
          variant="filled"
          onClick={handleRevert}
          className="action-btn-cancel"
          style={{ 
            flexShrink: 0,
            width: '24px',
            height: '24px',
            minWidth: '24px',
            minHeight: '24px'
          }}
        >
          <IconX size={12} />
        </ActionIcon>
      )}
      <ActionIcon
        size="sm"
        variant="filled"
        onClick={handleVerificationToggle}
        className={isVerified ? "action-btn-verify-yes verified" : "action-btn-verify-yes"}
        style={{ 
          flexShrink: 0,
          width: '24px',
          height: '24px',
          minWidth: '24px',
          minHeight: '24px'
        }}
      >
        <IconCheck size={12} />
      </ActionIcon>
    </Group>
  );
}

export function CompanyTable() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortStatus, setSortStatus] = useState<{
    columnAccessor: keyof Company;
    direction: 'asc' | 'desc';
  }>({ columnAccessor: 'company_name', direction: 'asc' });
  
  const [filters, setFilters] = useState<Record<keyof Company, string>>({
    company_name: '',
    state: '',
    investment_grade: '',
    investment_grade_summary: '',
    investment_grade_citations: '',
    est_annual_revenue: '',
    est_annual_revenue_citations: '',
    est_yoy_growth: '',
    est_yoy_growth_citations: '',
    pe_backed: '',
    pe_backed_citations: '',
    can_accommodate_allocation: '',
    can_accommodate_allocation_citations: '',
    good_reputation: '',
    good_reputation_citations: '',
    website: '',
    contact_info: '',
    annual_average_employees_2020: '',
    annual_average_employees_2021: '',
    annual_average_employees_2022: '',
    annual_average_employees_2023: '',
    annual_average_employees_2024: '',
    total_hours_worked_2020: '',
    total_hours_worked_2021: '',
    total_hours_worked_2022: '',
    total_hours_worked_2023: '',
    total_hours_worked_2024: '',
  });

  const [columnSettings, setColumnSettings] = useState<ColumnConfig[]>(() => {
    // Clear old settings by always using the updated columnConfigs
    return columnConfigs;
  });

  const [verifications, setVerifications] = useState<Record<string, Record<string, boolean>>>(() => {
    const savedVerifications = localStorage.getItem('companyTableVerifications');
    return savedVerifications ? JSON.parse(savedVerifications) : {};
  });

  const [cellEdits, setCellEdits] = useState<Record<string, Record<string, string>>>(() => {
    const savedEdits = localStorage.getItem('companyTableEdits');
    return savedEdits ? JSON.parse(savedEdits) : {};
  });

  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);

  useEffect(() => {
    localStorage.setItem('companyTableColumns', JSON.stringify(columnSettings));
  }, [columnSettings]);

  useEffect(() => {
    localStorage.setItem('companyTableVerifications', JSON.stringify(verifications));
  }, [verifications]);

  useEffect(() => {
    localStorage.setItem('companyTableEdits', JSON.stringify(cellEdits));
  }, [cellEdits]);

  const handleVerificationChange = (companyName: string, metricKey: string, verified: boolean) => {
    setVerifications(prev => ({
      ...prev,
      [companyName]: {
        ...prev[companyName],
        [metricKey]: verified
      }
    }));
  };

  const handleValueChange = (companyName: string, metricKey: string, newValue: string) => {
    setCellEdits(prev => ({
      ...prev,
      [companyName]: {
        ...prev[companyName],
        [metricKey]: newValue
      }
    }));
  };

  const handleRevert = (companyName: string, metricKey: string) => {
    setCellEdits(prev => {
      const newEdits = { ...prev };
      if (newEdits[companyName]) {
        delete newEdits[companyName][metricKey];
        if (Object.keys(newEdits[companyName]).length === 0) {
          delete newEdits[companyName];
        }
      }
      return newEdits;
    });
  };

  const transformCSVToCompany = (csvRow: CompanyCSV): Company => {
    const metrics: MetricData[] = JSON.parse(csvRow.Metrics);
    
    // Create a map for easy lookup
    const metricMap = new Map<string, MetricData>();
    metrics.forEach(metric => {
      metricMap.set(metric.metric_name, metric);
    });

    // Parse investment grade JSON to extract grade and summary
    let investmentGrade = 'Unknown';
    let investmentGradeSummary = '';
    let investmentGradeCitations: string[] = [];
    try {
      const gradeData = JSON.parse(csvRow["Investment Grade"]);
      investmentGrade = gradeData.grade || 'Unknown';
      investmentGradeSummary = gradeData.summary || '';
      investmentGradeCitations = gradeData.citations || [];
    } catch {
      // Fallback if not JSON format
      investmentGrade = csvRow["Investment Grade"];
      investmentGradeSummary = '';
    }

    // Transform to our expected format
    return {
      company_name: csvRow["Company Name"],
      state: csvRow["State"],
      investment_grade: investmentGrade,
      investment_grade_summary: investmentGradeSummary,
      investment_grade_citations: investmentGradeCitations,
      est_annual_revenue: metricMap.get('est_annual_revenue')?.metric?.toString() || 'Unknown',
      est_annual_revenue_citations: metricMap.get('est_annual_revenue')?.citations || [],
      est_yoy_growth: metricMap.get('est_yoy_growth')?.metric?.toString() || 'Unknown',
      est_yoy_growth_citations: metricMap.get('est_yoy_growth')?.citations || [],
      pe_backed: metricMap.get('pe_backed')?.metric === true ? 'Yes' : 'No',
      pe_backed_citations: metricMap.get('pe_backed')?.citations || [],
      can_accommodate_allocation: metricMap.get('can_accommodate_allocation')?.metric === true ? 'Yes' : 'No',
      can_accommodate_allocation_citations: metricMap.get('can_accommodate_allocation')?.citations || [],
      good_reputation: metricMap.get('reputation')?.metric?.toString() || 'Unknown',
      good_reputation_citations: metricMap.get('reputation')?.citations || [],
      // Add website and contact info
      website: csvRow["Website"] || '',
      contact_info: csvRow["Contact Info"] || '',
      // Add new employee and hours data from direct CSV columns
      annual_average_employees_2020: csvRow["annual_average_employees_2020"] || '',
      annual_average_employees_2021: csvRow["annual_average_employees_2021"] || '',
      annual_average_employees_2022: csvRow["annual_average_employees_2022"] || '',
      annual_average_employees_2023: csvRow["annual_average_employees_2023"] || '',
      annual_average_employees_2024: csvRow["annual_average_employees_2024"] || '',
      total_hours_worked_2020: csvRow["total_hours_worked_2020"] || '',
      total_hours_worked_2021: csvRow["total_hours_worked_2021"] || '',
      total_hours_worked_2022: csvRow["total_hours_worked_2022"] || '',
      total_hours_worked_2023: csvRow["total_hours_worked_2023"] || '',
      total_hours_worked_2024: csvRow["total_hours_worked_2024"] || '',
    };
  };

  useEffect(() => {
    fetch('/data.csv')
      .then((response) => response.text())
      .then((csvText) => {
        Papa.parse<CompanyCSV>(csvText, {
          header: true,
          skipEmptyLines: true,
          complete: (results) => {
            const transformedCompanies = results.data.map(transformCSVToCompany);
            setCompanies(transformedCompanies);
            setLoading(false);
          },
          error: (error: any) => {
            console.error('Error parsing CSV:', error);
            setLoading(false);
          }
        });
      })
      .catch((error) => {
        console.error('Error loading CSV:', error);
        setLoading(false);
      });
  }, []);

  const filteredAndSortedCompanies = useMemo(() => {
    let result = [...companies];

    Object.entries(filters).forEach(([key, filterValue]) => {
      if (filterValue) {
        result = result.filter((company) => {
          const value = company[key as keyof Company];
          if (Array.isArray(value)) {
            return value.some(item => item?.toLowerCase().includes(filterValue.toLowerCase()));
          }
          return value?.toString().toLowerCase().includes(filterValue.toLowerCase());
        });
      }
    });

    result.sort((a, b) => {
      const aVal = a[sortStatus.columnAccessor];
      const bVal = b[sortStatus.columnAccessor];
      const aStr = Array.isArray(aVal) ? aVal.join(' ') : aVal?.toString() || '';
      const bStr = Array.isArray(bVal) ? bVal.join(' ') : bVal?.toString() || '';
      
      const comparison = aStr.localeCompare(bStr, undefined, { numeric: true });
      return sortStatus.direction === 'asc' ? comparison : -comparison;
    });

    return result;
  }, [companies, filters, sortStatus]);


  const handleFilterChange = (column: keyof Company, value: string) => {
    setFilters(prev => ({ ...prev, [column]: value }));
  };

  const toggleColumnVisibility = (key: keyof Company) => {
    setColumnSettings(prev => 
      prev.map(col => 
        col.key === key ? { ...col, visible: !col.visible } : col
      )
    );
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const oldIndex = columnSettings.findIndex(col => col.key === active.id);
    const newIndex = columnSettings.findIndex(col => col.key === over.id);

    const newColumnSettings = [...columnSettings];
    const [movedItem] = newColumnSettings.splice(oldIndex, 1);
    newColumnSettings.splice(newIndex, 0, movedItem);

    newColumnSettings.forEach((col, index) => {
      col.order = index;
    });

    setColumnSettings(newColumnSettings);
  };

  const visibleColumns = columnSettings
    .filter(col => col.visible)
    .sort((a, b) => a.order - b.order);

  const columns: DataTableColumn<Company>[] = visibleColumns.map((colConfig, index) => ({
    accessor: colConfig.key,
    className: colConfig.group ? `grouped-column ${colConfig.group.replace(/\s+/g, '-').toLowerCase()}-group` : 
               index === 0 ? 'pinned-column sticky-first-column' : undefined,
    title: (
      <div 
        style={{ 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          width: '100%',
          background: colConfig.group === 'Avg Employees (OSHA)' ? 
            'linear-gradient(135deg, var(--eanna-electric-blue) 0%, var(--eanna-cyan) 100%)' : 
            colConfig.group === 'Total Hours Worked (OSHA)' ? 
            'linear-gradient(135deg, var(--eanna-cyan) 0%, var(--eanna-accent-gold) 100%)' : 
            'linear-gradient(135deg, var(--eanna-gray-800) 0%, var(--eanna-deep-blue) 100%)',
          color: 'var(--eanna-white)',
          padding: '12px 6px',
          fontWeight: colConfig.group ? 900 : 800,
          borderRadius: '0',
          textShadow: '0 1px 2px rgba(0,0,0,0.3)',
          boxShadow: colConfig.group ? '0 4px 8px rgba(0,0,0,0.15)' : '0 2px 4px rgba(0,0,0,0.1)',
          border: colConfig.group ? '2px solid rgba(255,255,255,0.2)' : '1px solid var(--eanna-gray-300)',
          ...(index === 0 ? {
            position: 'sticky',
            left: 0,
            zIndex: 20,
            borderRight: '2px solid rgba(44, 62, 80, 0.1)',
            boxShadow: '2px 0 4px rgba(0, 0, 0, 0.05), 0 2px 4px rgba(0, 0, 0, 0.1)'
          } : {})
        }}
      >
        {colConfig.group && (
          <Text 
            size="sm" 
            fw={900} 
            style={{ 
              userSelect: 'none', 
              color: 'var(--eanna-white)', 
              marginBottom: '4px',
              fontSize: '0.8rem',
              textShadow: '0 1px 2px rgba(0,0,0,0.4)',
              letterSpacing: '0.5px',
              textTransform: 'uppercase'
            }}
          >
            {colConfig.group}
          </Text>
        )}
        <Group gap={8} wrap="nowrap" style={{ width: '100%' }}>
          <SortableHeader id={colConfig.key}>
            <Text fw={colConfig.group ? 700 : 800} style={{ 
              color: 'var(--eanna-white)', 
              fontSize: colConfig.group ? '0.7rem' : '0.85rem',
              textShadow: '0 1px 2px rgba(0,0,0,0.3)',
              letterSpacing: '0.3px'
            }}>{colConfig.label}</Text>
          </SortableHeader>
          <Popover position="bottom" withArrow shadow="md">
            <Popover.Target>
              <ActionIcon 
                variant="subtle" 
                size="sm"
                style={{
                  color: 'var(--eanna-white)',
                  backgroundColor: 'rgba(255,255,255,0.15)',
                  borderRadius: '4px',
                  backdropFilter: 'blur(4px)'
                }}
              >
                <IconFilter size={12} />
              </ActionIcon>
            </Popover.Target>
            <Popover.Dropdown>
              <TextInput
                placeholder={`Filter ${colConfig.label}...`}
                value={filters[colConfig.key]}
                onChange={(e) => handleFilterChange(colConfig.key, e.currentTarget.value)}
                size="sm"
              />
            </Popover.Dropdown>
          </Popover>
        </Group>
      </div>
    ),
    render: (company) => {
      // Clean cell styling - no borders or backgrounds needed
      const cellStyle = {
        padding: '8px'
      };
      
      if (colConfig.type === 'definition') {
        if (colConfig.key === 'company_name') {
          return (
            <div 
              className="company-name-clickable"
              style={{ 
                ...cellStyle,
                fontSize: '0.875rem',
                fontFamily: 'var(--eanna-font-sans)'
              }}
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                setSelectedCompany(company);
              }}
            >
              {company[colConfig.key] as string}
            </div>
          );
        }
        return (
          <div style={cellStyle}>
            <Text size="sm" style={{ 
              color: 'var(--eanna-gray-700)', 
              fontWeight: 500,
              fontFamily: 'var(--eanna-font-sans)'
            }}>{company[colConfig.key] as string}</Text>
          </div>
        );
      } else {
        const citationKey = `${colConfig.key}_citations` as keyof Company;
        const citations = (company[citationKey] as string[]) || [];
        const isVerified = verifications[company.company_name]?.[colConfig.key] || false;
        const originalValue = company[colConfig.key] as string;
        const editedValue = cellEdits[company.company_name]?.[colConfig.key];
        const currentValue = editedValue !== undefined ? editedValue : originalValue;
        const isEdited = editedValue !== undefined;
        
        return (
          <div style={cellStyle}>
            <MetricCell
              value={currentValue}
              citations={citations}
              companyName={company.company_name}
              metricKey={colConfig.key}
              onVerificationChange={handleVerificationChange}
              isVerified={isVerified}
              onValueChange={handleValueChange}
              originalValue={originalValue}
              isEdited={isEdited}
              onRevert={handleRevert}
            />
          </div>
        );
      }
    },
    sortable: true,
  }));

  return (
    <Box style={{ width: '100%', maxWidth: 'none' }}>
      <div style={{ 
        display: 'flex', 
        gap: '1rem', 
        width: '100%',
        alignItems: 'flex-start'
      }}>
        {/* Main table container */}
        <div style={{ 
          flexGrow: 1,
          overflowX: 'auto', 
          width: selectedCompany ? '60%' : '100%',
          transition: 'width 0.3s ease',
          border: '1px solid var(--eanna-gray-200)'
        }}>
          <DndContext collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
            <SortableContext items={visibleColumns.map(col => col.key)} strategy={horizontalListSortingStrategy}>
              <DataTable
              records={filteredAndSortedCompanies}
              columns={columns}
              fetching={loading}
              sortStatus={sortStatus}
              onSortStatusChange={(status) => setSortStatus(status as any)}
              striped
              highlightOnHover
              withTableBorder
              withColumnBorders
              minHeight={500}
              borderRadius="0"
              shadow="none"
              storeColumnsKey="company-table-columns"
              scrollAreaProps={{
                style: { position: 'relative' }
              }}
              styles={{
                header: {
                  background: 'linear-gradient(135deg, var(--eanna-gray-800) 0%, var(--eanna-deep-blue) 100%)',
                  borderBottom: '3px solid var(--eanna-electric-blue)',
                  fontWeight: 800,
                  fontFamily: 'var(--eanna-font-sans)',
                  color: 'var(--eanna-white)',
                  padding: '8px 6px',
                  fontSize: '0.75rem',
                  height: 'auto',
                  lineHeight: '1.2',
                  textShadow: '0 1px 2px rgba(0,0,0,0.3)',
                  letterSpacing: '0.3px'
                },
                table: {
                  borderRadius: '8px',
                  overflow: 'hidden',
                  fontFamily: 'var(--eanna-font-sans)',
                  fontSize: '0.75rem',
                  tableLayout: 'auto',
                  width: '100%',
                  maxWidth: 'none',
                  boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
                  border: '1px solid var(--eanna-gray-300)'
                },
                root: {
                  width: '100%',
                  maxWidth: 'none',
                  borderRadius: '8px',
                  overflow: 'hidden'
                }
              }}
            />
            </SortableContext>
          </DndContext>

          {/* Customize View Button */}
          <Group justify="flex-end" mt="md">
            <Popover position="top-end" withArrow shadow="none">
              <Popover.Target>
                <Button 
                  leftSection={<IconSettings size={16} />}
                  size="sm"
                  className="professional-button"
                >
                  Customize View
                </Button>
              </Popover.Target>
              <Popover.Dropdown>
                <Stack gap="xs" p="sm">
                  <Text size="sm" fw={600} c="gray.8">Column Visibility</Text>
                  {columnSettings.map((col) => (
                    <Checkbox
                      key={col.key}
                      label={col.label}
                      checked={col.visible}
                      onChange={() => toggleColumnVisibility(col.key)}
                      size="sm"
                      styles={{
                        label: { fontWeight: 500 }
                      }}
                    />
                  ))}
                </Stack>
              </Popover.Dropdown>
            </Popover>
          </Group>
        </div>

        {/* Right-side Summary Panel */}
        {selectedCompany && (
          <div style={{ 
            width: '38%',
            minWidth: '400px',
            maxHeight: '80vh',
            border: '1px solid var(--eanna-gray-200)', 
            backgroundColor: 'var(--eanna-white)',
            flexShrink: 0,
            display: 'flex',
            flexDirection: 'column'
          }}>
            {/* Fixed Header */}
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'flex-start', 
              background: 'linear-gradient(135deg, var(--eanna-deep-blue) 0%, var(--eanna-electric-blue) 100%)',
              paddingBottom: '1.5rem',
              borderBottom: '3px solid var(--eanna-accent-gold)',
              paddingTop: '1.5rem',
              paddingLeft: '1.5rem',
              paddingRight: '1.5rem',
              boxShadow: '0 6px 20px rgba(0, 0, 0, 0.15)',
              flexShrink: 0
            }}>
              <div>
                <h2 style={{ 
                  fontFamily: 'var(--eanna-font-serif)',
                  color: 'var(--eanna-white)',
                  margin: 0,
                  fontSize: '1.4rem',
                  lineHeight: '1.2',
                  textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                  letterSpacing: '0.5px',
                  fontWeight: 700
                }}>
                  {selectedCompany.company_name}
                </h2>
                <span style={{ 
                  fontSize: '0.95rem',
                  fontWeight: 500,
                  color: 'var(--eanna-accent-gold)',
                  fontFamily: 'var(--eanna-font-sans)',
                  textShadow: '0 1px 2px rgba(0,0,0,0.2)',
                  letterSpacing: '0.3px'
                }}>
                  {(() => {
                    const stateNames = {
                      'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
                      'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
                      'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
                      'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
                      'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri',
                      'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
                      'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
                      'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
                      'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
                      'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming',
                      'DC': 'District of Columbia'
                    };
                    return stateNames[selectedCompany.state as keyof typeof stateNames] || selectedCompany.state;
                  })()}
                </span>
              </div>
              <button 
                onClick={() => setSelectedCompany(null)}
                style={{
                  background: 'rgba(255,255,255,0.15)',
                  border: '2px solid rgba(255,255,255,0.3)',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  color: 'var(--eanna-white)',
                  fontSize: '1.3rem',
                  padding: '8px 12px',
                  lineHeight: '1',
                  backdropFilter: 'blur(4px)',
                  transition: 'all 0.2s ease',
                  textShadow: '0 1px 2px rgba(0,0,0,0.3)'
                }}
                onMouseEnter={(e) => {
                  e.target.style.background = 'rgba(255,255,255,0.25)';
                  e.target.style.borderColor = 'rgba(255,255,255,0.5)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.background = 'rgba(255,255,255,0.15)';
                  e.target.style.borderColor = 'rgba(255,255,255,0.3)';
                }}
              >
                ✕
              </button>
            </div>

            {/* Scrollable Content */}
            <div style={{
              flex: 1,
              overflowY: 'auto',
              padding: '1.5rem'
            }}>

            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: '1fr', 
              gap: '0.75rem',
              marginBottom: '1.5rem',
              fontSize: '0.85rem'
            }}>
              <div>
                <strong style={{ color: 'var(--eanna-deep-blue)' }}>Investment Grade:</strong>{' '}
                <span style={{ 
                  color: 'var(--eanna-electric-blue)', 
                  fontWeight: 600,
                  fontSize: '0.9rem'
                }}>
                  {selectedCompany.investment_grade}
                </span>
              </div>
              {selectedCompany.website && (
                <div>
                  <strong style={{ color: 'var(--eanna-deep-blue)' }}>Website:</strong> 
                  <a 
                    href={selectedCompany.website.startsWith('http') ? selectedCompany.website : `https://${selectedCompany.website}`} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    style={{ marginLeft: '8px', color: 'var(--eanna-electric-blue)' }}
                  >
                    {selectedCompany.website}
                  </a>
                </div>
              )}
              <div>
                <strong style={{ color: 'var(--eanna-deep-blue)' }}>Est. Annual Revenue:</strong>{' '}
                <span style={{ 
                  color: 'var(--eanna-success-green)', 
                  fontWeight: 600,
                  fontSize: '0.9rem'
                }}>
                  {selectedCompany.est_annual_revenue}
                </span>
              </div>
              <div>
                <strong style={{ color: 'var(--eanna-deep-blue)' }}>Est. YoY Growth:</strong>{' '}
                <span style={{ 
                  color: 'var(--eanna-cyan)', 
                  fontWeight: 600,
                  fontSize: '0.9rem'
                }}>
                  {selectedCompany.est_yoy_growth}
                </span>
              </div>
              <div>
                <strong style={{ color: 'var(--eanna-deep-blue)' }}>PE-Backed:</strong>{' '}
                <span style={{ 
                  color: selectedCompany.pe_backed === 'Yes' ? 'var(--eanna-accent-gold)' : 'var(--eanna-gray-500)', 
                  fontWeight: 600,
                  fontSize: '0.9rem'
                }}>
                  {selectedCompany.pe_backed}
                </span>
              </div>
              <div>
                <strong style={{ color: 'var(--eanna-deep-blue)' }}>Can Accommodate $10M:</strong> {selectedCompany.can_accommodate_allocation}
              </div>
            </div>

            {/* Investment Grade Summary */}
            <div style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ 
                fontFamily: 'var(--eanna-font-serif)',
                color: 'var(--eanna-deep-blue)',
                marginBottom: '0.75rem',
                fontSize: '1.1rem'
              }}>
                Investment Grade Summary
              </h3>
              <div style={{
                padding: '1.25rem',
                background: 'linear-gradient(135deg, var(--eanna-gray-100) 0%, var(--eanna-light-blue) 100%)',
                border: '1px solid var(--eanna-gray-300)',
                borderLeft: '4px solid var(--eanna-electric-blue)',
                borderRadius: '6px',
                fontFamily: 'var(--eanna-font-sans)',
                fontSize: '0.85rem',
                lineHeight: '1.5',
                boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
              }}>
                {selectedCompany.investment_grade_summary || 'No summary available'}
              </div>
            </div>

            {/* OSHA Data Table */}
            <div style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ 
                fontFamily: 'var(--eanna-font-serif)',
                color: 'var(--eanna-deep-blue)',
                marginBottom: '0.75rem',
                fontSize: '1.1rem'
              }}>
                OSHA Data
              </h3>
              <table style={{ 
                width: '100%', 
                borderCollapse: 'collapse',
                fontFamily: 'var(--eanna-font-sans)',
                fontSize: '0.8rem',
                borderRadius: '6px',
                overflow: 'hidden',
                boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
              }}>
                <thead>
                  <tr>
                    <th style={{ 
                      padding: '10px 12px', 
                      borderBottom: '2px solid var(--eanna-electric-blue)',
                      textAlign: 'left',
                      background: 'linear-gradient(135deg, var(--eanna-electric-blue), var(--eanna-cyan))',
                      color: 'var(--eanna-white)',
                      fontWeight: 700,
                      textShadow: '0 1px 2px rgba(0,0,0,0.2)',
                      letterSpacing: '0.3px'
                    }}>Year</th>
                    <th style={{ 
                      padding: '10px 12px', 
                      borderBottom: '2px solid var(--eanna-electric-blue)',
                      textAlign: 'right',
                      background: 'linear-gradient(135deg, var(--eanna-electric-blue), var(--eanna-cyan))',
                      color: 'var(--eanna-white)',
                      fontWeight: 700,
                      textShadow: '0 1px 2px rgba(0,0,0,0.2)',
                      letterSpacing: '0.3px'
                    }}>Avg Employees</th>
                    <th style={{ 
                      padding: '10px 12px', 
                      borderBottom: '2px solid var(--eanna-electric-blue)',
                      textAlign: 'right',
                      background: 'linear-gradient(135deg, var(--eanna-electric-blue), var(--eanna-cyan))',
                      color: 'var(--eanna-white)',
                      fontWeight: 700,
                      textShadow: '0 1px 2px rgba(0,0,0,0.2)',
                      letterSpacing: '0.3px'
                    }}>Total Hours</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td style={{ padding: '8px 12px', borderBottom: '1px solid var(--eanna-gray-200)', fontWeight: 600, color: 'var(--eanna-gray-800)' }}>2024</td>
                    <td style={{ padding: '8px 12px', borderBottom: '1px solid var(--eanna-gray-200)', textAlign: 'right', fontWeight: 500, color: 'var(--eanna-gray-700)' }}>{selectedCompany.annual_average_employees_2024 || 'N/A'}</td>
                    <td style={{ padding: '8px 12px', borderBottom: '1px solid var(--eanna-gray-200)', textAlign: 'right', fontWeight: 500, color: 'var(--eanna-gray-700)' }}>{selectedCompany.total_hours_worked_2024 || 'N/A'}</td>
                  </tr>
                  <tr style={{ backgroundColor: 'var(--eanna-gray-50)' }}>
                    <td style={{ padding: '8px 12px', borderBottom: '1px solid var(--eanna-gray-200)', fontWeight: 600, color: 'var(--eanna-gray-800)' }}>2023</td>
                    <td style={{ padding: '8px 12px', borderBottom: '1px solid var(--eanna-gray-200)', textAlign: 'right', fontWeight: 500, color: 'var(--eanna-gray-700)' }}>{selectedCompany.annual_average_employees_2023 || 'N/A'}</td>
                    <td style={{ padding: '8px 12px', borderBottom: '1px solid var(--eanna-gray-200)', textAlign: 'right', fontWeight: 500, color: 'var(--eanna-gray-700)' }}>{selectedCompany.total_hours_worked_2023 || 'N/A'}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px 12px', borderBottom: '1px solid var(--eanna-gray-200)', fontWeight: 600, color: 'var(--eanna-gray-800)' }}>2022</td>
                    <td style={{ padding: '8px 12px', borderBottom: '1px solid var(--eanna-gray-200)', textAlign: 'right', fontWeight: 500, color: 'var(--eanna-gray-700)' }}>{selectedCompany.annual_average_employees_2022 || 'N/A'}</td>
                    <td style={{ padding: '8px 12px', borderBottom: '1px solid var(--eanna-gray-200)', textAlign: 'right', fontWeight: 500, color: 'var(--eanna-gray-700)' }}>{selectedCompany.total_hours_worked_2022 || 'N/A'}</td>
                  </tr>
                  <tr style={{ backgroundColor: 'var(--eanna-gray-50)' }}>
                    <td style={{ padding: '8px 12px', borderBottom: '1px solid var(--eanna-gray-200)', fontWeight: 600, color: 'var(--eanna-gray-800)' }}>2021</td>
                    <td style={{ padding: '8px 12px', borderBottom: '1px solid var(--eanna-gray-200)', textAlign: 'right', fontWeight: 500, color: 'var(--eanna-gray-700)' }}>{selectedCompany.annual_average_employees_2021 || 'N/A'}</td>
                    <td style={{ padding: '8px 12px', borderBottom: '1px solid var(--eanna-gray-200)', textAlign: 'right', fontWeight: 500, color: 'var(--eanna-gray-700)' }}>{selectedCompany.total_hours_worked_2021 || 'N/A'}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px 12px', fontWeight: 600, color: 'var(--eanna-gray-800)' }}>2020</td>
                    <td style={{ padding: '8px 12px', textAlign: 'right', fontWeight: 500, color: 'var(--eanna-gray-700)' }}>{selectedCompany.annual_average_employees_2020 || 'N/A'}</td>
                    <td style={{ padding: '8px 12px', textAlign: 'right', fontWeight: 500, color: 'var(--eanna-gray-700)' }}>{selectedCompany.total_hours_worked_2020 || 'N/A'}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Contact Information Section */}
            {selectedCompany.contact_info && (
              <div>
                <h3 style={{ 
                  fontFamily: 'var(--eanna-font-serif)',
                  color: 'var(--eanna-deep-blue)',
                  marginBottom: '0.75rem',
                  fontSize: '1.1rem'
                }}>
                  Contact Information
                </h3>
                <div style={{
                  padding: '0.875rem',
                  backgroundColor: 'var(--eanna-light-blue)',
                  border: '1px solid var(--eanna-gray-200)',
                  fontFamily: 'var(--eanna-font-sans)',
                  fontSize: '0.8rem',
                  lineHeight: '1.4'
                }}>
                  {(() => {
                    try {
                      const contacts = JSON.parse(selectedCompany.contact_info);
                      if (Array.isArray(contacts)) {
                        return (
                          <table style={{ 
                            width: 'auto', 
                            borderCollapse: 'collapse',
                            fontFamily: 'var(--eanna-font-sans)',
                            fontSize: '0.8rem'
                          }}>
                            <tbody>
                              {contacts.map((contact, index) => (
                                <tr key={index}>
                                  <td style={{ 
                                    padding: '3px 8px 3px 0', 
                                    verticalAlign: 'top',
                                    whiteSpace: 'nowrap'
                                  }}>
                                    <strong style={{ color: 'var(--eanna-deep-blue)' }}>
                                      {(contact.position || 'CONTACT').toUpperCase()}:
                                    </strong>{' '}
                                    {contact.first_name} {contact.last_name}
                                  </td>
                                  <td style={{ 
                                    padding: '3px 0', 
                                    verticalAlign: 'top'
                                  }}>
                                    {contact.email && (
                                      <>
                                        <strong>Email:</strong>{' '}
                                        <a 
                                          href={`mailto:${contact.email}`}
                                          style={{ color: 'var(--eanna-electric-blue)' }}
                                        >
                                          {contact.email}
                                        </a>
                                      </>
                                    )}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        );
                      } else {
                        return selectedCompany.contact_info;
                      }
                    } catch {
                      return selectedCompany.contact_info;
                    }
                  })()}
                </div>
              </div>
            )}
            </div>
          </div>
        )}
      </div>
    </Box>
  );
}