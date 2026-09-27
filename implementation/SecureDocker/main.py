import os
os.system("trivy image -f json -o result.json nginx")