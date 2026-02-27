import React, { useState, useEffect } from 'react';
import { getDemoFormats, previewDemoCSV, downloadDemoCSV } from '../api';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Label } from '../components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { Slider } from '../components/ui/slider';
import { Alert, AlertDescription } from '../components/ui/alert';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { Download, Eye, FileSpreadsheet, RefreshCw } from 'lucide-react';

const DemoGenerator = () => {
  const [formats, setFormats] = useState([]);
  const [selectedFormat, setSelectedFormat] = useState('quickbooks_online');
  const [numInvoices, setNumInvoices] = useState(5);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadFormats();
  }, []);

  const loadFormats = async () => {
    try {
      const data = await getDemoFormats();
      setFormats(data.formats);
    } catch (err) {
      console.error('Failed to load formats', err);
      // Use default formats if API fails
      setFormats([
        { key: 'quickbooks_online', name: 'QuickBooks Online' },
        { key: 'quickbooks_desktop', name: 'QuickBooks Desktop' },
        { key: 'xero', name: 'Xero' },
        { key: 'harvest', name: 'Harvest' },
        { key: 'freshbooks', name: 'FreshBooks' },
        { key: 'wave', name: 'Wave' },
        { key: 'generic', name: 'Generic CSV' }
      ]);
    }
  };

  const handlePreview = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await previewDemoCSV(selectedFormat, Math.min(numInvoices, 3));
      setPreview(data);
    } catch (err) {
      console.error('Failed to generate preview', err);
      setError('Failed to generate preview. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    setDownloading(true);
    setError('');
    try {
      const response = await downloadDemoCSV(selectedFormat, numInvoices);
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `demo_${selectedFormat}_${numInvoices}_invoices.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download CSV', err);
      setError('Failed to download CSV. Please try again.');
    } finally {
      setDownloading(false);
    }
  };

  const formatDescriptions = {
    quickbooks_online: 'Standard QuickBooks Online export format with columns like "Invoice #", "Customer", "Product/Service"',
    quickbooks_desktop: 'QuickBooks Desktop format with "Ref Number", "Trans Date", "Customer:Company" columns',
    xero: 'Xero accounting format with "Invoice ID", "Contact Name", "Unit Cost" columns',
    harvest: 'Harvest time tracking format with "Invoice Code", "Company", "Hours", "Hourly Rate"',
    freshbooks: 'FreshBooks format with "Invoice Number", "Client Name", "Units", "Price"',
    wave: 'Wave accounting format with "Invoice Identifier", "Business Name", "Extended Amount"',
    generic: 'Simple generic CSV format with standard column names'
  };

  return (
    <div className="space-y-6" data-testid="demo-generator-page">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Demo CSV Generator</h1>
        <p className="text-gray-500 mt-1">
          Generate sample CSV files to test the 180+ column mapping feature
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Configuration Card */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileSpreadsheet className="h-5 w-5" />
              Configuration
            </CardTitle>
            <CardDescription>
              Choose format and number of invoices
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label>Accounting Software Format</Label>
              <Select
                value={selectedFormat}
                onValueChange={setSelectedFormat}
                data-testid="format-select"
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select format" />
                </SelectTrigger>
                <SelectContent>
                  {formats.map((format) => (
                    <SelectItem key={format.key} value={format.key}>
                      {format.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-gray-500 mt-1">
                {formatDescriptions[selectedFormat]}
              </p>
            </div>

            <div className="space-y-2">
              <Label>Number of Invoices: {numInvoices}</Label>
              <Slider
                value={[numInvoices]}
                onValueChange={(value) => setNumInvoices(value[0])}
                min={1}
                max={20}
                step={1}
                className="mt-2"
                data-testid="invoice-count-slider"
              />
              <p className="text-xs text-gray-500">
                Each invoice contains 1-5 random line items
              </p>
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="flex gap-2">
              <Button
                onClick={handlePreview}
                variant="outline"
                disabled={loading}
                className="flex-1"
                data-testid="preview-btn"
              >
                {loading ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Eye className="h-4 w-4 mr-2" />
                )}
                Preview
              </Button>
              <Button
                onClick={handleDownload}
                disabled={downloading}
                className="flex-1"
                data-testid="download-btn"
              >
                {downloading ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Download className="h-4 w-4 mr-2" />
                )}
                Download
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Preview Card */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>CSV Preview</CardTitle>
            <CardDescription>
              {preview
                ? `${preview.format_name} format - ${preview.total_rows} rows`
                : 'Click "Preview" to see sample data'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {preview ? (
              <div className="space-y-4">
                <div className="overflow-x-auto border rounded-lg">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-gray-50">
                        {preview.headers.slice(0, 8).map((header, i) => (
                          <TableHead key={i} className="text-xs font-semibold whitespace-nowrap">
                            {header.replace(/"/g, '')}
                          </TableHead>
                        ))}
                        {preview.headers.length > 8 && (
                          <TableHead className="text-xs text-gray-400">
                            +{preview.headers.length - 8} more
                          </TableHead>
                        )}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {preview.sample_rows.map((row, i) => (
                        <TableRow key={i}>
                          {row.slice(0, 8).map((cell, j) => (
                            <TableCell key={j} className="text-xs whitespace-nowrap">
                              {cell.replace(/"/g, '').substring(0, 25)}
                              {cell.length > 25 ? '...' : ''}
                            </TableCell>
                          ))}
                          {row.length > 8 && (
                            <TableCell className="text-xs text-gray-400">...</TableCell>
                          )}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="text-sm font-medium mb-2">Raw CSV Preview</h4>
                  <pre className="text-xs text-gray-600 overflow-x-auto whitespace-pre-wrap font-mono bg-white p-3 rounded border max-h-48 overflow-y-auto">
                    {preview.csv_preview}
                  </pre>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <FileSpreadsheet className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>Select a format and click "Preview" to see sample data</p>
                <p className="text-sm mt-2">
                  The generator creates realistic invoice data with random companies,
                  services, and amounts
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Supported Formats Info */}
      <Card>
        <CardHeader>
          <CardTitle>Supported Accounting Software Formats</CardTitle>
          <CardDescription>
            InvoiceFlow can parse CSV exports from these popular accounting platforms
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
            {formats.map((format) => (
              <div
                key={format.key}
                className={`p-3 rounded-lg border text-center cursor-pointer transition-colors ${
                  selectedFormat === format.key
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }`}
                onClick={() => setSelectedFormat(format.key)}
              >
                <p className="text-sm font-medium">{format.name}</p>
              </div>
            ))}
          </div>
          <p className="text-sm text-gray-500 mt-4">
            <strong>180+ Column Variations Supported:</strong> Our intelligent CSV parser uses
            fuzzy matching to automatically detect and map columns from different accounting
            software exports, even when column names vary slightly.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default DemoGenerator;
