
import React from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Code } from "@/components/ui/code";
import { Separator } from "@/components/ui/separator";

const PythonProjectStructure = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Python Project Template</h1>
          <p className="text-xl text-gray-600">A clean, organized structure for your Python projects</p>
        </div>

        <Card className="mb-8">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Project Structure</CardTitle>
              <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">Best Practice</Badge>
            </div>
            <CardDescription>
              The recommended file and directory layout for a Python project
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="bg-gray-900 text-gray-100 p-4 rounded-md font-mono text-sm overflow-x-auto">
              <pre>
{`myproject/
├── README.md           # Project documentation
├── LICENSE            # Project license
├── setup.py           # Package and distribution management
├── requirements.txt   # Project dependencies
├── myproject/         # Source code package
│   ├── __init__.py    # Package initialization
│   ├── main.py        # Main module
│   └── utils.py       # Utility functions
└── tests/             # Test directory
    ├── __init__.py    # Test package initialization
    └── test_main.py   # Test cases for main module`}
              </pre>
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-8 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Core Files</CardTitle>
              <CardDescription>Essential files for your Python project</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h3 className="text-lg font-medium mb-2">README.md</h3>
                <Code className="text-xs">
{`# My Python Project

A brief description of your project.

## Installation

\`\`\`
pip install -r requirements.txt
\`\`\`

## Usage

\`\`\`python
from myproject import main

main.run()
\`\`\`
`}
                </Code>
              </div>
              
              <Separator />
              
              <div>
                <h3 className="text-lg font-medium mb-2">setup.py</h3>
                <Code className="text-xs">
{`from setuptools import setup, find_packages

setup(
    name="myproject",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Dependencies go here
    ],
    entry_points={
        'console_scripts': [
            'myproject=myproject.main:main',
        ],
    },
)
`}
                </Code>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>Source Files</CardTitle>
              <CardDescription>Key Python modules in your project</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h3 className="text-lg font-medium mb-2">main.py</h3>
                <Code className="text-xs">
{`"""
Main module for the application.
"""

def main():
    """Entry point for the application."""
    print("Hello, world!")
    
if __name__ == "__main__":
    main()
`}
                </Code>
              </div>
              
              <Separator />
              
              <div>
                <h3 className="text-lg font-medium mb-2">__init__.py</h3>
                <Code className="text-xs">
{`"""
My Python project.

A brief description of what the project does.
"""

__version__ = "0.1.0"
`}
                </Code>
              </div>
            </CardContent>
          </Card>
        </div>
        
        <div className="mt-8 text-center">
          <Button className="bg-blue-600 hover:bg-blue-700">
            <a href="https://docs.python.org/3/tutorial/modules.html" target="_blank" rel="noopener noreferrer" className="text-white">
              Learn More About Python Modules
            </a>
          </Button>
        </div>
      </div>
    </div>
  );
};

export default PythonProjectStructure;
