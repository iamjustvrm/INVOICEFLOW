import React, { useState, useEffect } from 'react';
import { getBranding, updateBranding } from '../api';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Label } from '../components/ui/label';
import { Input } from '../components/ui/input';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Save, Palette } from 'lucide-react';

const Settings = () => {
  const [branding, setBranding] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadBranding();
  }, []);

  const loadBranding = async () => {
    try {
      const data = await getBranding();
      setBranding(data);
    } catch (error) {
      console.error('Failed to load branding', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateBranding(branding);
      setMessage('Branding settings saved successfully!');
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Failed to save branding', error);
      alert('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading settings...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500 mt-1">Customize your invoice branding</p>
      </div>

      {message && (
        <Alert className="border-green-200 bg-green-50">
          <AlertDescription className="text-green-800">{message}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Palette className="h-5 w-5" />
            Branding Customization
          </CardTitle>
          <CardDescription>
            Customize colors and fonts for your invoices
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <Label htmlFor="primary-color">Primary Color</Label>
              <div className="flex gap-3 items-center mt-2">
                <Input
                  id="primary-color"
                  type="color"
                  value={branding?.primary_color || '#3B82F6'}
                  onChange={(e) => setBranding({ ...branding, primary_color: e.target.value })}
                  className="w-20 h-10"
                />
                <Input
                  type="text"
                  value={branding?.primary_color || '#3B82F6'}
                  onChange={(e) => setBranding({ ...branding, primary_color: e.target.value })}
                  placeholder="#3B82F6"
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">Used for headers and accents</p>
            </div>

            <div>
              <Label htmlFor="secondary-color">Secondary Color</Label>
              <div className="flex gap-3 items-center mt-2">
                <Input
                  id="secondary-color"
                  type="color"
                  value={branding?.secondary_color || '#1E40AF'}
                  onChange={(e) => setBranding({ ...branding, secondary_color: e.target.value })}
                  className="w-20 h-10"
                />
                <Input
                  type="text"
                  value={branding?.secondary_color || '#1E40AF'}
                  onChange={(e) => setBranding({ ...branding, secondary_color: e.target.value })}
                  placeholder="#1E40AF"
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">Used for secondary elements</p>
            </div>
          </div>

          <div>
            <Label htmlFor="font-family">Font Family</Label>
            <select
              id="font-family"
              className="w-full border border-gray-300 rounded-md px-3 py-2 mt-2"
              value={branding?.font_family || 'Inter'}
              onChange={(e) => setBranding({ ...branding, font_family: e.target.value })}
            >
              <option value="Inter">Inter</option>
              <option value="Helvetica">Helvetica</option>
              <option value="Arial">Arial</option>
              <option value="Times New Roman">Times New Roman</option>
              <option value="Georgia">Georgia</option>
              <option value="Roboto">Roboto</option>
            </select>
          </div>

          <div className="pt-4 border-t">
            <h3 className="text-lg font-semibold mb-4">Preview</h3>
            <div className="border rounded-lg p-6" style={{ borderColor: branding?.primary_color }}>
              <div
                className="text-2xl font-bold mb-4"
                style={{ color: branding?.primary_color, fontFamily: branding?.font_family }}
              >
                INVOICE
              </div>
              <div className="space-y-2" style={{ fontFamily: branding?.font_family }}>
                <div className="text-sm text-gray-600">Invoice Number: INV-001</div>
                <div className="text-sm text-gray-600">Date: {new Date().toLocaleDateString()}</div>
                <div className="text-sm text-gray-600">Client: Acme Corp</div>
              </div>
              <div
                className="mt-4 p-3 rounded"
                style={{ backgroundColor: branding?.primary_color + '20' }}
              >
                <div className="text-sm" style={{ fontFamily: branding?.font_family }}>
                  This is how your invoice will look with these settings.
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <Button onClick={handleSave} disabled={saving}>
              <Save className="h-4 w-4 mr-2" />
              {saving ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Settings;
