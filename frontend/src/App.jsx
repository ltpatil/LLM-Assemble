import { useState, useEffect } from 'react'
import axios from 'axios'
import {
  Box, Container, Input, Button, VStack, Heading, Text, Card, CardBody,
  Divider, Alert, AlertIcon,
  Accordion, AccordionItem, AccordionButton, AccordionPanel, AccordionIcon,
  Stat, StatLabel, StatNumber, Tag, HStack, useToast, Fade,
  Progress, Grid, GridItem,
  Drawer, DrawerBody, DrawerHeader, DrawerOverlay, DrawerContent, DrawerCloseButton,
  useDisclosure, Badge, IconButton
} from '@chakra-ui/react'
import { SearchIcon, TimeIcon, DeleteIcon } from '@chakra-ui/icons'

const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
const API_URL = `${BASE_URL}/api`
const API_TOKEN = import.meta.env.VITE_API_TOKEN || ""

function App() {
  const [prompt, setPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [history, setHistory] = useState([])

  const { isOpen, onOpen, onClose } = useDisclosure()
  const toast = useToast()

  const fetchHistory = async () => {
    try {
      const response = await axios.get(`${API_URL}/history`)
      setHistory(response.data)
    } catch (err) {
      console.error("Failed to load history", err)
    }
  }

  const deleteHistoryItem = async (e, id) => {
    e.stopPropagation()
    try {
      await axios.delete(`${API_URL}/history/${id}`, { headers: { Authorization: `Bearer ${API_TOKEN}` } })
      setHistory(prev => prev.filter(item => item.id !== id))
      toast({ title: "Deleted", status: "success", duration: 1000, size: "sm" })
    } catch (err) {
      toast({ title: "Error", description: "Could not delete item", status: "error" })
    }
  }

  useEffect(() => {
    if (isOpen) fetchHistory()
  }, [isOpen])

  const handleSearch = async () => {
    if (!prompt.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await axios.post(
        `${API_URL}/aggregate`,
        { prompt: prompt },
        { headers: { Authorization: `Bearer ${API_TOKEN}` } }
      )
      setResult(response.data)
      fetchHistory()
    } catch (err) {
      const msg = err.response?.data?.detail || "Failed to connect to the Aggregator API"
      setError(msg)
      toast({ title: "Connection Error", description: msg, status: "error", duration: 5000, isClosable: true })
    } finally {
      setLoading(false)
    }
  }
  // Load a past result into the main view
  const loadHistoryItem = (item) => {
    setPrompt(item.prompt)

    // Parse the JSON strings back into Arrays
    // If the data is missing (old DB records), default to empty arrays []
    let parsedCandidates = [];
    let parsedSnippets = [];

    try {
      parsedCandidates = item.all_candidates_json ? JSON.parse(item.all_candidates_json) : [];
      parsedSnippets = item.evidence_snippets_json ? JSON.parse(item.evidence_snippets_json) : [];
    } catch (e) {
      console.error("Error parsing history JSON", e);
    }

    setResult({
      winner: {
        response: {
          provider_name: item.winning_provider,
          text: item.winning_text,
          model_name: "Archive"
        },
        final_score: item.final_score,
        evidence_score: item.evidence_score,
        consensus_score: item.consensus_score,
        sentiment_score: item.sentiment_score,
        evidence_snippets: parsedSnippets // <--- Now contains the real snippets!
      },
      all_candidates: parsedCandidates,   // <--- Now contains the real candidate list!
      explainability: "Loaded from History Archive"
    })
    onClose()
  }

  const getScoreColor = (score) => {
    if (score >= 0.7) return "green"
    if (score >= 0.4) return "yellow"
    return "red"
  }

  return (
    <Box minH="100vh" bg="white" color="gray.800" py={20} position="relative">

      <Box position="absolute" top={6} right={6}>
        <Button leftIcon={<TimeIcon />} variant="ghost" onClick={onOpen} colorScheme="gray">
          History
        </Button>
      </Box>

      <Container maxW="container.md">

        <VStack spacing={2} mb={10} align="center">
          <Heading as="h1" size="2xl" letterSpacing="tight" fontWeight="800">
            LLMASSEMBLE
          </Heading>
          <Text fontSize="md" color="gray.500" letterSpacing="wide" >
            Evidence-Based Aggregation Engine
          </Text>
        </VStack>

        <VStack spacing={4} w="100%" mb={10}>
          <Input
            size="lg" placeholder="Type your question here..." value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            isDisabled={loading} borderRadius="full" focusBorderColor="black"
            bg="gray.50" border="1px solid" borderColor="gray.200" py={6} boxShadow="sm"
          />
          <Button
            size="lg" w="100%" borderRadius="full" bg="black" color="white"
            _hover={{ bg: 'gray.800' }} onClick={handleSearch}
            isLoading={loading} loadingText="Processing" leftIcon={<SearchIcon />}
          >
            Ask LLMASSEMBLE
          </Button>
        </VStack>

        {error && <Alert status="error" variant="subtle" borderRadius="md" mb={6}><AlertIcon />{error}</Alert>}

        {result && (
          <Fade in={true}>
            <Box>
              <Card variant="unstyled" mb={6}>
                <CardBody p={0}>
                  <Text fontSize="xl" lineHeight="1.6" fontWeight="500">{result.winner?.response.text}</Text>
                </CardBody>
              </Card>

              <Accordion allowToggle border="1px solid" borderColor="gray.100" borderRadius="lg" defaultIndex={[0]}>
                <AccordionItem border="none">
                  <h2>
                    <AccordionButton _hover={{ bg: 'gray.50' }} borderRadius="lg">
                      <Box flex='1' textAlign='left' fontSize="sm" fontWeight="600" color="gray.500">View Detailed Analysis</Box>
                      <AccordionIcon color="gray.400" />
                    </AccordionButton>
                  </h2>
                  <AccordionPanel pb={6} pt={2}>

                    {/* WINNER METRICS */}
                    <HStack mb={6} justify="space-between" align="center">
                      <Tag size="md" variant="subtle" colorScheme="purple">Source: {result.winner?.response.provider_name}</Tag>
                      <VStack align="end" spacing={0}>
                        <Text fontSize="xs" color="gray.400" textTransform="uppercase">Confidence</Text>
                        <Text fontSize="lg" fontWeight="bold" color="blue.600">{(result.winner?.final_score * 100).toFixed(1)}%</Text>
                      </VStack>
                    </HStack>

                    <Grid templateColumns="repeat(3, 1fr)" gap={4} mb={8}>
                      {['Evidence', 'Consensus', 'Sentiment'].map((label, idx) => {
                        const score = idx === 0 ? result.winner?.evidence_score : idx === 1 ? result.winner?.consensus_score : result.winner?.sentiment_score;
                        return (
                          <GridItem key={label} bg="gray.50" p={3} borderRadius="md">
                            <Stat>
                              <StatLabel fontSize="xs" color="gray.500">{label}</StatLabel>
                              <StatNumber fontSize="lg">{(score * 100).toFixed(0)}</StatNumber>
                              <Progress value={score * 100} size="xs" colorScheme={getScoreColor(score)} mt={2} borderRadius="full" />
                            </Stat>
                          </GridItem>
                        )
                      })}
                    </Grid>

                    {/* EVIDENCE */}
                    {result.winner?.evidence_snippets && result.winner?.evidence_snippets.length > 0 && (
                      <Box mb={8}>
                        <Text fontSize="xs" fontWeight="bold" color="gray.400" textTransform="uppercase" mb={3}>Verified Context</Text>
                        <VStack align="stretch" spacing={2}>
                          {result.winner.evidence_snippets.map((snip, i) => (
                            <Text key={i} fontSize="xs" color="gray.600" bg="gray.50" p={3} borderRadius="md" borderLeft="3px solid" borderColor="blue.200">"{snip.substring(0, 200)}..."</Text>
                          ))}
                        </VStack>
                      </Box>
                    )}

                    {/* ALL CANDIDATES BREAKDOWN */}
                    {result.all_candidates?.length > 0 && (
                      <Box>
                        <Text fontSize="xs" fontWeight="bold" color="gray.400" textTransform="uppercase" mb={3}>Full Candidate Comparison</Text>
                        <VStack align="stretch" spacing={4}>
                          {result.all_candidates?.map((cand) => (
                            <Box
                              key={cand.candidate_id} p={4}
                              bg={cand.candidate_id === result.winner.candidate_id ? "blue.50" : "white"}
                              border="1px solid"
                              borderColor={cand.candidate_id === result.winner.candidate_id ? "blue.200" : "gray.200"}
                              borderRadius="md"
                            >
                              <HStack justify="space-between" mb={2}>
                                <HStack>
                                  <Badge colorScheme={cand.candidate_id === result.winner.candidate_id ? "blue" : "gray"}>
                                    {cand.response.provider_name}
                                  </Badge>
                                  {cand.candidate_id === result.winner.candidate_id && <Badge colorScheme="green">WINNER</Badge>}
                                </HStack>
                                <Text fontSize="xs" fontWeight="bold" color="gray.500">Total Score: {cand.final_score.toFixed(2)}</Text>
                              </HStack>

                              <Text fontSize="sm" color="gray.700" mb={3}>{cand.response.text}</Text>

                              {/* DETAILED MINI SCORES */}
                              <HStack spacing={4} pt={2} borderTop="1px dashed" borderColor="gray.200">
                                <VStack align="start" spacing={0}>
                                  <Text fontSize="10px" color="gray.400" textTransform="uppercase">Evidence</Text>
                                  <Text fontSize="xs" fontWeight="bold">{cand.evidence_score.toFixed(2)}</Text>
                                </VStack>
                                <VStack align="start" spacing={0}>
                                  <Text fontSize="10px" color="gray.400" textTransform="uppercase">Consensus</Text>
                                  <Text fontSize="xs" fontWeight="bold">{cand.consensus_score.toFixed(2)}</Text>
                                </VStack>
                                <VStack align="start" spacing={0}>
                                  <Text fontSize="10px" color="gray.400" textTransform="uppercase">Sentiment</Text>
                                  <Text fontSize="xs" fontWeight="bold">{cand.sentiment_score.toFixed(2)}</Text>
                                </VStack>
                              </HStack>
                            </Box>
                          ))}
                        </VStack>
                      </Box>
                    )}

                  </AccordionPanel>
                </AccordionItem>
              </Accordion>
            </Box>
          </Fade>
        )}
      </Container>

      {/* --- HISTORY SIDEBAR (DRAWER) --- */}
      <Drawer isOpen={isOpen} placement='right' onClose={onClose} size="md">
        <DrawerOverlay />
        <DrawerContent bg="gray.50">
          <DrawerCloseButton />
          <DrawerHeader borderBottomWidth='1px'>Research History</DrawerHeader>
          <DrawerBody>
            <VStack spacing={4} align="stretch" mt={4}>
              {history.length === 0 && <Text color="gray.500" textAlign="center">No history found yet.</Text>}
              {history.map((item) => (
                <Card
                  key={item.id}
                  cursor="pointer"
                  onClick={() => loadHistoryItem(item)}
                  _hover={{ transform: 'scale(1.02)', shadow: 'md' }}
                  transition="all 0.2s"
                  bg="white"
                >
                  <CardBody p={4}>
                    <HStack justify="space-between" align="start" mb={2}>
                      <Badge colorScheme="blue">Score: {item.final_score.toFixed(2)}</Badge>
                      <IconButton
                        icon={<DeleteIcon />}
                        size="xs"
                        colorScheme="red"
                        variant="ghost"
                        aria-label="Delete item"
                        onClick={(e) => deleteHistoryItem(e, item.id)}
                      />
                    </HStack>

                    <Text fontWeight="bold" fontSize="sm" noOfLines={2} mb={2} color="gray.700">{item.prompt}</Text>

                    <HStack justify="space-between">
                      <Text fontSize="xs" color="gray.400">{new Date(item.timestamp).toLocaleDateString()}</Text>
                      <Tag size="sm" variant="subtle">{item.winning_provider}</Tag>
                    </HStack>
                  </CardBody>
                </Card>
              ))}
            </VStack>
          </DrawerBody>
        </DrawerContent>
      </Drawer>
    </Box>
  )
}

export default App