import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getInvoice, updateInvoice, generatePDF } from '../api';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Label } from '../components/ui/label';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import { ArrowLeft, FileText, Save } from 'lucide-react';
import { Alert, AlertDescription } from '../components/ui/alert';

const InvoiceDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [invoice, setInvoice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadInvoice();
  }, [id]);

  const loadInvoice = async () => {
    try {
      const data = await getInvoice(id);
      setInvoice(data);
    } catch (error) {
      console.error('Failed to load invoice', error);
      alert('Invoice not found');
      navigate('/invoices');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateInvoice(id, invoice);
      setMessage('Invoice updated successfully!');
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Failed to update invoice', error);
      alert('Failed to update invoice');
    } finally {
      setSaving(false);
    }
  };

  const handleGeneratePDF = async () => {
    try {
      await generatePDF(id);
      setMessage('PDF generated successfully!');
      loadInvoice();
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Failed to generate PDF', error);
      alert('Failed to generate PDF');
    }
  };

  const updateLineItem = (index, field, value) => {
    const newLineItems = [...invoice.line_items];
    newLineItems[index] = { ...newLineItems[index], [field]: value };

    // Recalculate amount if quantity or rate changes
    if (field === 'quantity' || field === 'rate') {
      const qty = field === 'quantity' ? parseFloat(value) : newLineItems[index].quantity;
      const rate = field === 'rate' ? parseFloat(value) : newLineItems[index].rate;
      newLineItems[index].amount = qty * rate;
    }

    // Recalculate totals
    const subtotal = newLineItems.reduce((sum, item) => sum + (item.amount || 0), 0);
    const tax_amount = subtotal * (invoice.tax_rate / 100);
    const total = subtotal + tax_amount;

    setInvoice({
      ...invoice,
      line_items: newLineItems,
      subtotal,
      tax_amount,
      total
    });
  };

  const handleViewPDF = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}${invoice.pdf_url}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to load PDF');
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      window.open(url, '_blank');
    } catch (error) {
      console.error('Failed to view PDF', error);
      alert('Failed to view PDF. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading invoice...</div>
      </div>
    );
  }

  if (!invoice) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => navigate('/invoices')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{invoice.invoice_number}</h1>
            <p className="text-gray-500 mt-1">{invoice.client_name}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button onClick={handleSave} disabled={saving}>
            <Save className="h-4 w-4 mr-2" />
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
          {!invoice.pdf_url ? (
            <Button onClick={handleGeneratePDF} variant="outline">
              <FileText className="h-4 w-4 mr-2" />
              Generate PDF
            </Button>
          ) : (
            <Button
              onClick={() => window.open(`${process.env.REACT_APP_BACKEND_URL}${invoice.pdf_url}`, '_blank')}
              variant="outline"
            >
              View PDF
            </Button>
          )}
        </div>
      </div>

      {message && (
        <Alert className="border-green-200 bg-green-50">
          <AlertDescription className="text-green-800">{message}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Invoice Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Invoice Number</Label>
              <Input
                value={invoice.invoice_number}
                onChange={(e) => setInvoice({ ...invoice, invoice_number: e.target.value })}
              />
            </div>
            <div>
              <Label>Invoice Date</Label>
              <Input
                type="date"
                value={invoice.invoice_date?.split('T')[0] || ''}
                onChange={(e) => setInvoice({ ...invoice, invoice_date: e.target.value })}
              />
            </div>
            <div>
              <Label>Due Date</Label>
              <Input
                type="date"
                value={invoice.due_date?.split('T')[0] || ''}
                onChange={(e) => setInvoice({ ...invoice, due_date: e.target.value })}
              />
            </div>
            <div>
              <Label>Status</Label>
              <select
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                value={invoice.status}
                onChange={(e) => setInvoice({ ...invoice, status: e.target.value })}
              >
                <option value="draft">Draft</option>
                <option value="sent">Sent</option>
                <option value="paid">Paid</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Client Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Client Name</Label>
              <Input
                value={invoice.client_name}
                onChange={(e) => setInvoice({ ...invoice, client_name: e.target.value })}
              />
            </div>
            <div>
              <Label>Email</Label>
              <Input
                type="email"
                value={invoice.client_email || ''}
                onChange={(e) => setInvoice({ ...invoice, client_email: e.target.value })}
              />
            </div>
            <div>
              <Label>Address</Label>
              <Textarea
                value={invoice.client_address || ''}
                onChange={(e) => setInvoice({ ...invoice, client_address: e.target.value })}
                rows={3}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Line Items</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {invoice.line_items.map((item, index) => (
              <div key={index} className="grid grid-cols-12 gap-3 p-4 bg-gray-50 rounded-lg">
                <div className="col-span-5">
                  <Label className="text-xs">Description</Label>
                  <Input
                    value={item.description}
                    onChange={(e) => updateLineItem(index, 'description', e.target.value)}
                  />
                </div>
                <div className="col-span-2">
                  <Label className="text-xs">Quantity</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={item.quantity}
                    onChange={(e) => updateLineItem(index, 'quantity', e.target.value)}
                  />
                </div>
                <div className="col-span-2">
                  <Label className="text-xs">Rate</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={item.rate}
                    onChange={(e) => updateLineItem(index, 'rate', e.target.value)}
                  />
                </div>
                <div className="col-span-3">
                  <Label className="text-xs">Amount</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={item.amount.toFixed(2)}
                    readOnly
                    className="bg-white"
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 flex justify-end">
            <div className="w-64 space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Subtotal:</span>
                <span className="font-semibold">${invoice.subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Tax ({invoice.tax_rate.toFixed(2)}%):</span>
                <span className="font-semibold">${invoice.tax_amount.toFixed(2)}</span>
              </div>
              <div className="flex justify-between pt-2 border-t-2 border-blue-600">
                <span className="text-lg font-bold text-blue-600">Total:</span>
                <span className="text-lg font-bold text-blue-600">${invoice.total.toFixed(2)}</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {invoice.notes && (
        <Card>
          <CardHeader>
            <CardTitle>Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <Textarea
              value={invoice.notes}
              onChange={(e) => setInvoice({ ...invoice, notes: e.target.value })}
              rows={4}
            />
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default InvoiceDetail;
