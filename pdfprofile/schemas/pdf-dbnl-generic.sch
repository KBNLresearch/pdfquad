<?xml version="1.0"?>
<!--
   Schematron schema for DBNL PDFs: verify if PDF conforms to 
   KB requirements. 
-->
<s:schema xmlns:s="http://purl.oclc.org/dsdl/schematron">


<s:pattern>
    <s:title>DBNL PDFs</s:title>

    <!-- check of resolutiewaarden juist zijn (marge van +/- 5 ppi) -->
    <s:rule context="/properties/pdfimages/image">
        <s:assert test="(x-ppi &gt; 299) and
        (x-ppi &lt; 301)">horizontale resolutie niet binnen acceptabele marges</s:assert>
        <s:assert test="(y-ppi &gt; 299) and 
        (y-ppi &lt; 301)">verticale resolutie niet binnen acceptabele marges</s:assert>
    </s:rule>

</s:pattern>
</s:schema>

