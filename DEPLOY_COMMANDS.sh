#!/bin/bash
# Complete GitHub Deployment Commands
# Repository: https://github.com/mikedconcepcion/momentumfx-research

echo "=========================================="
echo "DEPLOYING TO GITHUB"
echo "=========================================="
echo ""

# Navigate to dist folder
cd "D:/Coding_Workspace/SD_Trend_Universal_Research/dist"

# Stage all changes
echo "Staging all files..."
git add .

# Commit with comprehensive message
echo "Committing changes..."
git commit -m "Complete package: 6-year validation with GitHub Pages

Research Package:
- 6-year validation (2020-2025) including COVID-19 crash
- 2.4M bars analyzed, 130 zones detected
- Pattern strengthened during COVID (2.80x concentration)
- Gold confirmed as PRIMARY instrument (95.3% OB concentration)
- All periods statistically significant (p<0.001)

GitHub Pages:
- Professional landing page with interactive charts
- Mobile-responsive design
- SVG charts for period and instrument comparison
- Comprehensive methodology and data sections

Documentation:
- SIX_YEAR_VALIDATION_2020_2025.md (comprehensive analysis)
- Updated README.md with 6-year results
- Updated CHANGELOG.md
- Academic paper (55KB, peer-review ready)
- 9 research documents total

Data: Dukascopy Bank SA
License: MIT - Open Source
Contact: momentumfxtrading25@gmail.com"

# Push to GitHub
echo "Pushing to GitHub..."
git push origin main

echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Go to: https://github.com/mikedconcepcion/momentumfx-research"
echo "2. Click 'Settings' → 'Pages'"
echo "3. Set Source: 'main' branch, Folder: '/docs'"
echo "4. Click 'Save'"
echo "5. Wait 2-5 minutes for deployment"
echo "6. Visit: https://mikedconcepcion.github.io/momentumfx-research/"
echo ""
echo "=========================================="
