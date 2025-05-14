'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';

export default function TestingGuidePage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-2xl font-bold mb-6">Testing & Validation Guide</h1>
      <p className="text-muted-foreground mb-8">
        This guide will help you test and validate various features of the ChatSphere platform.
      </p>
      
      <Tabs defaultValue="widget" className="w-full">
        <TabsList className="mb-6 w-full justify-start">
          <TabsTrigger value="widget">Widget Testing</TabsTrigger>
          <TabsTrigger value="integrations">Integrations</TabsTrigger>
          <TabsTrigger value="datasources">Data Sources</TabsTrigger>
          <TabsTrigger value="troubleshooting">Troubleshooting</TabsTrigger>
        </TabsList>
        
        <TabsContent value="widget">
          <Card>
            <CardHeader>
              <CardTitle>Testing Chatbot Widget/Embed</CardTitle>
              <CardDescription>
                Follow these steps to verify your chatbot widget is working correctly
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Accordion type="single" collapsible className="w-full">
                <AccordionItem value="step1">
                  <AccordionTrigger>Step 1: Generate Embed Code</AccordionTrigger>
                  <AccordionContent>
                    <ol className="list-decimal pl-5 space-y-2">
                      <li>Go to your chatbot's configuration page by clicking on a chatbot in the dashboard</li>
                      <li>Navigate to the "Embed" tab</li>
                      <li>Customize your widget settings (position, color, title)</li>
                      <li>Click "Generate Embed Code"</li>
                      <li>The code should look like:<br />
                        <pre className="bg-muted p-2 rounded mt-2 text-xs overflow-x-auto">
                          {`<script 
  src="http://localhost:3000/widget/YOUR_CHATBOT_ID.js" 
  data-chatbot-id="YOUR_CHATBOT_ID"
  data-position="bottom-right"
  data-primary-color="6366f1"
  data-title="Chat Assistant"
  data-show-branding="true"
></script>`}
                        </pre>
                      </li>
                    </ol>
                  </AccordionContent>
                </AccordionItem>
                
                <AccordionItem value="step2">
                  <AccordionTrigger>Step 2: Preview Widget In-App</AccordionTrigger>
                  <AccordionContent>
                    <p className="mb-2">The easiest way to test your widget is using the new "Preview Widget" button:</p>
                    <ol className="list-decimal pl-5 space-y-2">
                      <li>On your chatbot's configuration page, find the "Preview Widget" button next to the embed code</li>
                      <li>Click this button to activate a test widget directly in the ChatSphere application</li>
                      <li>The widget should appear in the position you specified with your chosen colors and title</li>
                      <li>Test sending messages to verify the chatbot responds correctly</li>
                      <li>You can remove the test widget using the "Remove Test Widget" button in the notification</li>
                    </ol>
                  </AccordionContent>
                </AccordionItem>
                
                <AccordionItem value="step3">
                  <AccordionTrigger>Step 3: Test on External Website</AccordionTrigger>
                  <AccordionContent>
                    <p className="mb-2">To fully test the widget on an external site:</p>
                    <ol className="list-decimal pl-5 space-y-2">
                      <li>Create a simple HTML file on your computer, like <code>test.html</code></li>
                      <li>Add basic HTML structure and paste your embed code in the <code>&lt;body&gt;</code> section</li>
                      <li>Make sure the URL in the embed code points to your running ChatSphere instance</li>
                      <li>Open the HTML file in a browser</li>
                      <li>The chatbot widget button should appear in the specified position</li>
                      <li>Click the button to open the chat interface</li>
                      <li>Test sending messages to verify connectivity</li>
                    </ol>
                    <div className="bg-muted p-3 rounded mt-2">
                      <p className="font-medium mb-1">Sample test.html file:</p>
                      <pre className="text-xs overflow-x-auto">
{`<!DOCTYPE html>
<html>
<head>
  <title>ChatSphere Widget Test</title>
</head>
<body>
  <h1>Widget Test Page</h1>
  <p>Your widget should appear in the bottom-right corner.</p>
  
  <!-- Paste your embed code here -->
  <script 
    src="http://localhost:3000/widget/YOUR_CHATBOT_ID.js" 
    data-chatbot-id="YOUR_CHATBOT_ID"
    data-position="bottom-right"
    data-primary-color="6366f1"
    data-title="Chat Assistant"
    data-show-branding="true"
  ></script>
</body>
</html>`}
                      </pre>
                    </div>
                  </AccordionContent>
                </AccordionItem>
                
                <AccordionItem value="troubleshooting">
                  <AccordionTrigger>Troubleshooting Widget Issues</AccordionTrigger>
                  <AccordionContent>
                    <p className="font-medium mb-2">Common issues and solutions:</p>
                    <ul className="list-disc pl-5 space-y-2">
                      <li><strong>Widget doesn't appear:</strong> Check browser console for errors. Ensure both frontend and backend servers are running.</li>
                      <li><strong>Widget appears but doesn't connect:</strong> Check if the chatbot ID is correct and the backend server is accessible.</li>
                      <li><strong>CORS errors in console:</strong> Ensure the backend has proper CORS settings for your domain.</li>
                      <li><strong>Widget loads but messages fail:</strong> Check authentication settings and verify the API endpoints for the chat sessions.</li>
                    </ul>
                    <p className="mt-3">To see detailed debug logs, add <code>?debug=true</code> to your test page URL.</p>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="integrations">
          <Card>
            <CardHeader>
              <CardTitle>Testing Integrations</CardTitle>
              <CardDescription>
                How to validate various integrations with external platforms
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Accordion type="single" collapsible className="w-full">
                <AccordionItem value="slack">
                  <AccordionTrigger>Slack Integration</AccordionTrigger>
                  <AccordionContent>
                    <ol className="list-decimal pl-5 space-y-2">
                      <li>Create a Slack app in your workspace through the <a href="https://api.slack.com/apps" className="text-primary underline" target="_blank" rel="noopener noreferrer">Slack API Dashboard</a></li>
                      <li>Enable Incoming Webhooks in your app settings</li>
                      <li>Create a new webhook URL for a specific channel</li>
                      <li>Copy the webhook URL to the Slack integration tab in ChatSphere</li>
                      <li>To test: Send a test message in the Slack integration page</li>
                      <li>Verify the message appears in your Slack channel</li>
                    </ol>
                  </AccordionContent>
                </AccordionItem>
                
                <AccordionItem value="discord">
                  <AccordionTrigger>Discord Integration</AccordionTrigger>
                  <AccordionContent>
                    <ol className="list-decimal pl-5 space-y-2">
                      <li>Go to your Discord server settings and navigate to the Integrations tab</li>
                      <li>Create a webhook for the channel you want to connect to</li>
                      <li>Copy the webhook URL to the Discord integration tab in ChatSphere</li>
                      <li>To test: Send a test message in the Discord integration page</li>
                      <li>Verify the message appears in your Discord channel</li>
                    </ol>
                  </AccordionContent>
                </AccordionItem>
                
                <AccordionItem value="email">
                  <AccordionTrigger>Email Integration</AccordionTrigger>
                  <AccordionContent>
                    <ol className="list-decimal pl-5 space-y-2">
                      <li>Configure your email settings in the Email integration tab</li>
                      <li>Add the email address that will send/receive messages</li>
                      <li>Configure SMTP settings if required</li>
                      <li>To test: Send a test email through the integration page</li>
                      <li>Check your inbox for the test message</li>
                    </ol>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="datasources">
          <Card>
            <CardHeader>
              <CardTitle>Testing Data Sources</CardTitle>
              <CardDescription>
                Validate that your data sources are working correctly
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Accordion type="single" collapsible className="w-full">
                <AccordionItem value="upload">
                  <AccordionTrigger>Uploading & Processing Data Sources</AccordionTrigger>
                  <AccordionContent>
                    <ol className="list-decimal pl-5 space-y-2">
                      <li>Go to the Data Sources tab in the dashboard</li>
                      <li>Click "Upload New Document" and select a test file (PDF, TXT, DOCX, CSV)</li>
                      <li>Add a name and description for your document</li>
                      <li>Submit the form and wait for processing to complete</li>
                      <li>The status should change from "processing" to "ready" when complete</li>
                    </ol>
                    <div className="bg-blue-50 p-3 rounded mt-3 text-blue-800">
                      <p><strong>Tip:</strong> Start with smaller documents (1-5 pages) to ensure faster processing times during testing.</p>
                    </div>
                  </AccordionContent>
                </AccordionItem>
                
                <AccordionItem value="delete">
                  <AccordionTrigger>Deleting Data Sources</AccordionTrigger>
                  <AccordionContent>
                    <ol className="list-decimal pl-5 space-y-2">
                      <li>Find a document you want to delete in the Data Sources list</li>
                      <li>Click the trash icon button on the document card</li>
                      <li>Confirm deletion in the dialog that appears</li>
                      <li>The document should be removed from the list immediately</li>
                      <li>If the document is being used by a chatbot, you might receive a warning</li>
                    </ol>
                    <div className="bg-yellow-50 p-3 rounded mt-3 text-yellow-800">
                      <p><strong>Important:</strong> Deleting a data source removes it permanently and from all chatbots using it. This action cannot be undone.</p>
                    </div>
                  </AccordionContent>
                </AccordionItem>
                
                <AccordionItem value="verify">
                  <AccordionTrigger>Verifying Data Source Usage</AccordionTrigger>
                  <AccordionContent>
                    <ol className="list-decimal pl-5 space-y-2">
                      <li>Create a chatbot that uses one or more of your data sources</li>
                      <li>Go to the chatbot's playground</li>
                      <li>Ask questions about specific information contained in your data source</li>
                      <li>The chatbot should be able to answer with relevant information</li>
                      <li>Check if the sources are cited correctly in the responses</li>
                    </ol>
                    <div className="bg-green-50 p-3 rounded mt-3 text-green-800">
                      <p><strong>Example questions to ask:</strong></p>
                      <ul className="list-disc pl-5 mt-1">
                        <li>"What is mentioned about [specific topic] in my document?"</li>
                        <li>"Summarize the main points from [document name]"</li>
                        <li>"What does page 5 of my document discuss?"</li>
                      </ul>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="troubleshooting">
          <Card>
            <CardHeader>
              <CardTitle>Common Issues & Troubleshooting</CardTitle>
              <CardDescription>
                Solutions for frequent problems when using ChatSphere
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Accordion type="single" collapsible className="w-full">
                <AccordionItem value="backend">
                  <AccordionTrigger>Backend Connection Issues</AccordionTrigger>
                  <AccordionContent>
                    <ul className="space-y-3">
                      <li className="bg-muted p-3 rounded">
                        <strong>Error:</strong> "Failed to fetch" or network errors<br/>
                        <strong>Solution:</strong> Ensure the backend server is running on port 8000. Check terminal for any errors in the backend logs.
                      </li>
                      <li className="bg-muted p-3 rounded">
                        <strong>Error:</strong> "CORS policy" errors in console<br/>
                        <strong>Solution:</strong> Verify CORS settings in the backend allow requests from your frontend origin.
                      </li>
                      <li className="bg-muted p-3 rounded">
                        <strong>Error:</strong> HTTP 401 Unauthorized errors<br/>
                        <strong>Solution:</strong> Check if your auth token is valid and being sent correctly in API requests.
                      </li>
                    </ul>
                    <div className="mt-4">
                      <p className="font-medium">Command to restart backend:</p>
                      <pre className="bg-muted p-2 rounded text-xs mt-1">cd backend && python -m src.main --port 8000</pre>
                    </div>
                  </AccordionContent>
                </AccordionItem>
                
                <AccordionItem value="widget">
                  <AccordionTrigger>Widget/Embed Issues</AccordionTrigger>
                  <AccordionContent>
                    <ul className="space-y-3">
                      <li className="bg-muted p-3 rounded">
                        <strong>Error:</strong> Widget script doesn't load<br/>
                        <strong>Solution:</strong> Make sure both frontend and backend services are running. Check your browser's console for specific errors.
                      </li>
                      <li className="bg-muted p-3 rounded">
                        <strong>Error:</strong> Widget appears but chat doesn't work<br/>
                        <strong>Solution:</strong> Check if the backend API for chat sessions is functioning. Try restarting the backend server.
                      </li>
                      <li className="bg-muted p-3 rounded">
                        <strong>Error:</strong> Script loads but widget doesn't appear<br/>
                        <strong>Solution:</strong> Inspect the page for any CSS conflicts. Try modifying the data-position attribute in the embed code.
                      </li>
                    </ul>
                  </AccordionContent>
                </AccordionItem>
                
                <AccordionItem value="data">
                  <AccordionTrigger>Data Source Issues</AccordionTrigger>
                  <AccordionContent>
                    <ul className="space-y-3">
                      <li className="bg-muted p-3 rounded">
                        <strong>Error:</strong> Document stays in "processing" status<br/>
                        <strong>Solution:</strong> Check backend logs for processing errors. Try uploading a smaller or different format document.
                      </li>
                      <li className="bg-muted p-3 rounded">
                        <strong>Error:</strong> "Cannot read properties of undefined" when viewing documents<br/>
                        <strong>Solution:</strong> Ensure document objects have all required properties. Check for null values in API responses.
                      </li>
                      <li className="bg-muted p-3 rounded">
                        <strong>Error:</strong> Document fails to delete<br/>
                        <strong>Solution:</strong> Verify the API endpoint for document deletion is working. Check if the document is in use by any chatbots.
                      </li>
                    </ul>
                  </AccordionContent>
                </AccordionItem>
                
                <AccordionItem value="reset">
                  <AccordionTrigger>Resetting Your Environment</AccordionTrigger>
                  <AccordionContent>
                    <p className="mb-3">If you encounter persistent issues, try these reset steps:</p>
                    <ol className="list-decimal pl-5 space-y-2">
                      <li>Clear your browser cache and local storage</li>
                      <li>Restart both frontend and backend servers</li>
                      <li>Check for any error logs in both terminal windows</li>
                      <li>Verify Firebase emulator is running (if using local development)</li>
                      <li>Ensure all environment variables are set correctly</li>
                    </ol>
                    <div className="bg-red-50 p-3 rounded mt-3 text-red-800">
                      <p><strong>Last resort:</strong> If all else fails, you can reset your local database by stopping all services, clearing Firebase emulator data, and restarting.</p>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
} 