import json

# TODO make modular, break out subsections, all these wonderful things
def generate_html_report(results):
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Results Report</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <style>
            .success {{ background-color: #d4edda; }}
            .failure {{ background-color: #f8d7da; }}
            pre {{ white-space: pre-wrap; word-wrap: break-word; max-height: 200px; overflow-y: auto; }}
        </style>
    </head>
    <body>
        <div class="container mt-4">
            <h2>Test Results Summary</h2>
            <p>
                Successful Queries: {success_count} / {total_count}
                ({success_percentage:.1f}%)
            </p>
            
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>Test Case</th>
                        <th>Result</th>
                        <th>Details</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """

    row_template = """
    <tr class="{row_class}">
        <td class="col-md-2">{case_name}</td>
        <td class="col-md-1">{result}</td>
        <td>
            <div class="accordion" id="accordion_{case_id}">
                <div class="accordion-item">
                    <h2 class="accordion-header">
                        <button class="accordion-button collapsed" type="button" 
                                data-bs-toggle="collapse" 
                                data-bs-target="#query_{case_id}">
                            Query
                        </button>
                    </h2>
                    <div id="query_{case_id}" class="accordion-collapse collapse">
                        <div class="accordion-body">
                            <pre>{query}</pre>
                        </div>
                    </div>
                </div>
                
                <div class="accordion-item">
                    <h2 class="accordion-header">
                        <button class="accordion-button collapsed" type="button" 
                                data-bs-toggle="collapse" 
                                data-bs-target="#data_{case_id}">
                            Data
                        </button>
                    </h2>
                    <div id="data_{case_id}" class="accordion-collapse collapse">
                        <div class="accordion-body">
                            <pre>{case_data}</pre>
                        </div>
                    </div>
                </div>

                <div class="accordion-item">
                    <h2 class="accordion-header">
                        <button class="accordion-button collapsed" type="button" 
                                data-bs-toggle="collapse" 
                                data-bs-target="#response_{case_id}">
                            {response_title}
                        </button>
                    </h2>
                    <div id="response_{case_id}" class="accordion-collapse collapse">
                        <div class="accordion-body">
                            <pre>{response}</pre>
                        </div>
                    </div>
                </div>
            </div>
        </td>
    </tr>
    """

    rows = []
    success_count = 0
    
    for i, result in enumerate(results):
        is_success = result["result"] == "Success"
        if is_success:
            success_count += 1
            
        row = row_template.format(
            row_class="success" if is_success else "failure",
            case_id=i,
            case_name=result["case"].name,
            case_data=json.dumps(result["case"].documents, indent=2),
            result=result["result"],
            query=result["case"].query,
            response_title="Response" if is_success else "Error",
            response=json.dumps(result["body"], indent=2) if is_success else 
                    f"Error Source: {result.get('err_source', 'unknown')}\n{result.get('err', 'Unknown error')}"
        )
        rows.append(row)

    total_count = len(results)
    success_percentage = (success_count / total_count * 100) if total_count > 0 else 0

    html_content = html_template.format(
        success_count=success_count,
        total_count=total_count,
        success_percentage=success_percentage,
        table_rows="\n".join(rows),
    )

    with open("test_report.html", "w") as f:
        f.write(html_content)
