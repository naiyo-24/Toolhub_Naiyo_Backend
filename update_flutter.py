import re

file_path = "/Users/sayarpaul/Project/Toolhub_Naiyo/lib/features/loandesk/presentation/screens/cases/case_workspace_screen.dart"
with open(file_path, "r") as f:
    content = f.read()

# 1. Add imports if not present
if "import 'package:dio/dio.dart';" not in content:
    content = content.replace("import 'package:flutter/material.dart';", "import 'package:flutter/material.dart';\nimport 'package:dio/dio.dart';\nimport 'package:path_provider/path_provider.dart';\nimport 'package:open_filex/open_filex.dart';\nimport '../../../../core/api/api_config.dart';\nimport 'package:shared_preferences/shared_preferences.dart';")

# 2. Add the download function inside the _CaseWorkspaceScreenState class
download_func = """
  Future<void> _downloadAndOpenReport(BuildContext context, String caseId, String caseNumber) async {
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Generating PDF Report...')));
    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('access_token');
      
      final dir = await getApplicationDocumentsDirectory();
      final filePath = '${dir.path}/Case_Report_$caseNumber.pdf';
      
      final dio = Dio();
      if (token != null) {
        dio.options.headers['Authorization'] = 'Bearer $token';
      }
      
      await dio.download(
        '${ApiConfig.loanDeskBaseUrl}/cases/$caseId/download-report',
        filePath,
      );
      
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Report downloaded successfully!')));
      await OpenFilex.open(filePath);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to download report: $e')));
    }
  }

  @override
  Widget build(BuildContext context) {
"""

if "_downloadAndOpenReport" not in content:
    content = content.replace("  @override\n  Widget build(BuildContext context) {", download_func)

# 3. Add the IconButton to the AppBar row
icon_button = """
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.picture_as_pdf, color: LoanDeskTheme.primaryBlue),
                    tooltip: "Download PDF Report",
                    onPressed: () => _downloadAndOpenReport(context, loanCase.id.toString(), loanCase.caseNumber),
                  ),
                ],
              ),
"""

old_row_end = """
                      ],
                    ),
                  ),
                ],
              ),
"""

content = content.replace(old_row_end, icon_button)

with open(file_path, "w") as f:
    f.write(content)
print("Flutter UI updated successfully!")
