import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Paper,
  Breadcrumbs,
  Link,
  CircularProgress,
  Alert,
  Collapse,
  Divider,
  TextField,
  InputAdornment,
} from '@mui/material';
import {
  PlayArrow as PlayArrowIcon,
  Person as PersonIcon,
  Code as CodeIcon,
  AdminPanelSettings as AdminPanelSettingsIcon,
  MenuBook as MenuBookIcon,
  ExpandLess,
  ExpandMore,
  Search as SearchIcon,
  Home as HomeIcon,
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface DocItem {
  title: string;
  path: string;
  description?: string;
}

interface DocSection {
  title: string;
  icon: string;
  items: DocItem[];
}

interface NavigationData {
  sections: DocSection[];
}

const iconMap: { [key: string]: React.ReactElement } = {
  PlayArrow: <PlayArrowIcon />,
  Person: <PersonIcon />,
  Code: <CodeIcon />,
  AdminPanelSettings: <AdminPanelSettingsIcon />,
  MenuBook: <MenuBookIcon />,
};

const Documentation: React.FC = () => {
  const [navigation, setNavigation] = useState<NavigationData | null>(null);
  const [currentDoc, setCurrentDoc] = useState<string>('');
  const [currentPath, setCurrentPath] = useState<string>('index.md');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['Getting Started'])
  );
  const [searchQuery, setSearchQuery] = useState<string>('');

  useEffect(() => {
    loadNavigation();
    loadDocument('index.md');
  }, []);

  const loadNavigation = async () => {
    try {
      const response = await fetch('/docs/nav.json');
      if (!response.ok) throw new Error('Failed to load navigation');
      const data = await response.json();
      setNavigation(data);
    } catch (err) {
      console.error('Error loading navigation:', err);
      setError('Failed to load documentation navigation');
    }
  };

  const loadDocument = async (path: string) => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`/docs/${path}`);
      if (!response.ok) throw new Error('Document not found');
      const text = await response.text();
      setCurrentDoc(text);
      setCurrentPath(path);
    } catch (err) {
      console.error('Error loading document:', err);
      setError('Failed to load document');
      setCurrentDoc('# Document Not Found\n\nThe requested document could not be loaded.');
    } finally {
      setLoading(false);
    }
  };

  const toggleSection = (sectionTitle: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionTitle)) {
      newExpanded.delete(sectionTitle);
    } else {
      newExpanded.add(sectionTitle);
    }
    setExpandedSections(newExpanded);
  };

  const handleDocumentClick = (path: string) => {
    loadDocument(path);
    window.scrollTo(0, 0);
  };

  const getBreadcrumbs = () => {
    if (!navigation) return [];
    
    const parts = currentPath.split('/');
    const crumbs: { label: string; path?: string }[] = [
      { label: 'Documentation', path: 'index.md' }
    ];

    if (parts.length > 1) {
      // Find the section
      for (const section of navigation.sections) {
        const item = section.items.find(i => i.path === currentPath);
        if (item) {
          crumbs.push({ label: section.title });
          crumbs.push({ label: item.title });
          break;
        }
      }
    }

    return crumbs;
  };

  const filterSections = (): NavigationData | null => {
    if (!navigation || !searchQuery) return navigation;

    const query = searchQuery.toLowerCase();
    const filteredSections = navigation.sections
      .map(section => ({
        ...section,
        items: section.items.filter(item =>
          item.title.toLowerCase().includes(query) ||
          item.description?.toLowerCase().includes(query)
        )
      }))
      .filter(section => section.items.length > 0);

    return { sections: filteredSections };
  };

  const displayNavigation = filterSections();

  return (
    <Box sx={{ display: 'flex', height: 'calc(100vh - 64px)' }}>
      {/* Left Sidebar - Navigation */}
      <Paper
        sx={{
          width: 280,
          height: '100%',
          overflow: 'auto',
          borderRadius: 0,
          borderRight: 1,
          borderColor: 'divider',
        }}
      >
        <Box sx={{ p: 2 }}>
          <TextField
            fullWidth
            size="small"
            placeholder="Search docs..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
            }}
          />
        </Box>

        {displayNavigation && (
          <List dense>
            {displayNavigation.sections.map((section) => (
              <React.Fragment key={section.title}>
                <ListItemButton onClick={() => toggleSection(section.title)}>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    {iconMap[section.icon] || <MenuBookIcon />}
                  </ListItemIcon>
                  <ListItemText
                    primary={section.title}
                    primaryTypographyProps={{ fontWeight: 600, fontSize: '0.9rem' }}
                  />
                  {expandedSections.has(section.title) ? <ExpandLess /> : <ExpandMore />}
                </ListItemButton>
                <Collapse in={expandedSections.has(section.title)} timeout="auto">
                  <List dense disablePadding>
                    {section.items.map((item) => (
                      <ListItem key={item.path} disablePadding>
                        <ListItemButton
                          sx={{
                            pl: 7,
                            bgcolor: currentPath === item.path ? 'action.selected' : 'transparent',
                          }}
                          onClick={() => handleDocumentClick(item.path)}
                        >
                          <ListItemText
                            primary={item.title}
                            primaryTypographyProps={{ fontSize: '0.85rem' }}
                          />
                        </ListItemButton>
                      </ListItem>
                    ))}
                  </List>
                </Collapse>
                <Divider />
              </React.Fragment>
            ))}
          </List>
        )}
      </Paper>

      {/* Main Content */}
      <Box sx={{ flexGrow: 1, overflow: 'auto', bgcolor: 'background.default' }}>
        <Container maxWidth="md" sx={{ py: 4 }}>
          {/* Breadcrumbs */}
          <Breadcrumbs sx={{ mb: 3 }} separator="›">
            {getBreadcrumbs().map((crumb, index) => (
              crumb.path ? (
                <Link
                  key={index}
                  underline="hover"
                  color="inherit"
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    if (crumb.path) handleDocumentClick(crumb.path);
                  }}
                  sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
                >
                  {index === 0 && <HomeIcon fontSize="small" />}
                  {crumb.label}
                </Link>
              ) : (
                <Typography key={index} color="text.primary">
                  {crumb.label}
                </Typography>
              )
            ))}
          </Breadcrumbs>

          {/* Error Alert */}
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          {/* Loading Spinner */}
          {loading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
              <CircularProgress />
            </Box>
          )}

          {/* Documentation Content */}
          {!loading && currentDoc && (
            <Paper sx={{ p: 4 }}>
              <ReactMarkdown
                components={{
                  code({ node, className, children, ...props }: any) {
                    const match = /language-(\w+)/.exec(className || '');
                    const inline = !match;
                    return !inline && match ? (
                      <SyntaxHighlighter
                        style={vscDarkPlus as any}
                        language={match[1]}
                        PreTag="div"
                        {...props}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    ) : (
                      <code
                        className={className}
                        style={{
                          backgroundColor: '#f5f5f5',
                          padding: '2px 6px',
                          borderRadius: '3px',
                          fontSize: '0.9em',
                        }}
                        {...props}
                      >
                        {children}
                      </code>
                    );
                  },
                  h1: ({ children }) => (
                    <Typography variant="h3" gutterBottom sx={{ mt: 4, mb: 2 }}>
                      {children}
                    </Typography>
                  ),
                  h2: ({ children }) => (
                    <Typography variant="h4" gutterBottom sx={{ mt: 3, mb: 2 }}>
                      {children}
                    </Typography>
                  ),
                  h3: ({ children }) => (
                    <Typography variant="h5" gutterBottom sx={{ mt: 2, mb: 1 }}>
                      {children}
                    </Typography>
                  ),
                  p: ({ children }) => (
                    <Typography paragraph sx={{ lineHeight: 1.7 }}>
                      {children}
                    </Typography>
                  ),
                  ul: ({ children }) => (
                    <Box component="ul" sx={{ pl: 3, my: 2 }}>
                      {children}
                    </Box>
                  ),
                  ol: ({ children }) => (
                    <Box component="ol" sx={{ pl: 3, my: 2 }}>
                      {children}
                    </Box>
                  ),
                  li: ({ children }) => (
                    <Typography component="li" sx={{ mb: 0.5 }}>
                      {children}
                    </Typography>
                  ),
                  table: ({ children }) => (
                    <Box sx={{ overflowX: 'auto', my: 2 }}>
                      <Box
                        component="table"
                        sx={{
                          width: '100%',
                          borderCollapse: 'collapse',
                          '& th': {
                            bgcolor: 'primary.main',
                            color: 'primary.contrastText',
                            p: 1.5,
                            textAlign: 'left',
                            fontWeight: 600,
                          },
                          '& td': {
                            borderBottom: 1,
                            borderColor: 'divider',
                            p: 1.5,
                          },
                        }}
                      >
                        {children}
                      </Box>
                    </Box>
                  ),
                  blockquote: ({ children }) => (
                    <Box
                      sx={{
                        borderLeft: 4,
                        borderColor: 'primary.main',
                        bgcolor: 'action.hover',
                        p: 2,
                        my: 2,
                        fontStyle: 'italic',
                      }}
                    >
                      {children}
                    </Box>
                  ),
                }}
              >
                {currentDoc}
              </ReactMarkdown>
            </Paper>
          )}
        </Container>
      </Box>
    </Box>
  );
};

export default Documentation;
