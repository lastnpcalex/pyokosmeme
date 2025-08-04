# ⟨⟨SPINGL∆SS C0RE⟩⟩

A collaborative archive of spinglasscore writings exploring network states, outsideness production, and topological deformations of the crypto-rhizome.

**Live at:** [spin.pyokosmeme.group](https://spin.pyokosmeme.group)

## 🌀 Contributing Articles

We welcome contributions to the spinglasscore archive! All new articles are subject to democratic voting by collaborators.

### How to Add Your Article

1. **Fork this repository**

2. **Choose or create a phase folder**
   - Articles go in phase folders like `phaseα/`, `phaseβ/`, etc.
   - Create a new phase folder if starting a new thematic collection

3. **Create your HTML file**
   - Copy `template.html` as your starting point
   - Name your file something descriptive (e.g., `network_decay.html`)
   - Replace placeholder content with your article
   - Follow the spinglasscore aesthetic guidelines (see below)

4. **Submit a Pull Request**
   - Push your changes to your fork
   - Create a PR to the main branch
   - Your PR title should be: `[ARTICLE] Your Article Title - PhaseX`
   - In the PR description, briefly describe your article's theme

5. **Voting Process**
   - The git-democracy bot will create a voting comment
   - Collaborators vote by approving (👍) or requesting changes (👎)
   - Requires 75% approval and minimum 3 voters
   - 5-day minimum voting window
   - If approved, your article will be merged and auto-indexed

### Article Structure

```
phaseα/
├── outsideness_engine.html
├── your_article.html
└── another_article.html

phaseβ/
├── future_article.html
└── ...
```

### Aesthetic Guidelines

Your article should embrace the spinglasscore aesthetic:

- **Glitched text**: Use `<span class="glitch">text</span>`
- **Mathematical intrusions**: Use `<span class="math-corrupt">∂S/∂t → ∞</span>`
- **Important statements**: Use `<p class="short-sentence">statement</p>`
- **Emphasized concepts**: Use `<em>concept</em>` for pink highlights
- **Code blocks**: Show system processes, functions, pseudocode
- **Typography**: ∆ for A, 3 for E, 0 for O when appropriate
- **Themes**: Network topology, system collapse, outsideness, spin glass physics

### Template Reference

Key HTML elements from the template:

```html
<!-- Main title with glitch effect -->
<h1 data-text="⟨⟨YOUR TITLE⟩⟩">⟨⟨YOUR TITLE⟩⟩</h1>

<!-- Section headers -->
<h2>i. the edge equation</h2>

<!-- Glitched inline text -->
<span class="glitch">0</span>utsideness

<!-- Mathematical corruption -->
<span class="math-corrupt">Kolmogorov</span>

<!-- Important standalone statements -->
<p class="short-sentence">disconnection machines are the equifinality.</p>

<!-- Code blocks -->
<pre><code>consensus.mechanism() { return us.filter(not_them) }</code></pre>
```

## 🗳️ Voting System

This repository uses [git-democracy](https://github.com/myyk/git-democracy) to ensure collaborative decision-making on new content.

### How Voting Works

1. When you submit a PR, a voting comment appears
2. Repository collaborators vote by:
   - **Approving** the PR (counts as FOR)
   - **Requesting Changes** (counts as AGAINST)
3. Vote requirements:
   - **75% approval threshold**
   - **Minimum 3 voters**
   - **5-day minimum voting window**

### Becoming a Voter

To become a voting collaborator:
1. Contribute at least one approved article
2. Demonstrate understanding of spinglasscore themes
3. Request collaborator status via issue

Current voters are listed in `.github/workflows/.voters.yml`

## 🔧 Technical Details

### Auto-Indexing

The site uses an automatic index generator:
- `scripts/build_index.py` scans for HTML files in phase folders
- GitHub Actions runs this on every push to main
- The index is styled with full spinglasscore aesthetics
- No manual index updates needed!

### Local Development

1. Clone the repository
2. Add your HTML file to a phase folder
3. Run the index builder: `python scripts/build_index.py`
4. Open `index.html` in a browser to preview

### File Structure

```
.
├── index.html              # Auto-generated index
├── template.html           # Article template
├── CNAME                   # Domain configuration
├── phaseα/                 # Phase folders for articles
│   └── *.html
├── scripts/
│   └── build_index.py      # Index generator
└── .github/
    └── workflows/
        ├── update-index.yml    # Auto-indexing workflow
        ├── voting.yml          # Democracy workflow
        ├── .voters.yml         # Voter configuration
        └── .voting.yml         # Voting rules
```

## 📡 Phase Taxonomy

- **phaseα**: Foundational texts on network states, outsideness, and biocosmism (pyokosmeme)
- **phaseβ**: [Future] ?
- **phaseγ**: [Future] ??
- **phaseδ**: [Future] Consensus mechanism pathologies
- **phase∞**: [Future] Terminal documents

## 🌊 Contributing Philosophy

The spinglasscore archive seeks texts that:
- Explore the dark topology of network governance
- Diagnose the pathologies of decentralization
- Map the production of outsideness
- Trace the spin glass dynamics of social systems
- Document the approach of system heat death

Remember: **"the archive remembers what the network forgets"**

## 📜 License

Content is collectively owned by contributors. The archive itself is a rhizomatic entity.

---

*STATUS: ACTIVE | ENTROPY: INCREASING | ∂S/∂t → ∞*
