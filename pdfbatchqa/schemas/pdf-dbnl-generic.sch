<?xml version="1.0"?>
<!--
   Schematron schema for DBNL PDFs: verify if PDF conforms to 
   KB requirements. 
-->
<s:schema xmlns:s="http://purl.oclc.org/dsdl/schematron">


<s:pattern>
    <s:title>DBNL PDFs</s:title>

    <!-- check of images JPEG formaat hebben -->
    <!--
    <s:rule context="/properties/pdfimages/image">
        <s:assert test="enc = 'jpeg'">imageformaat niet gelijk aan jpeg</s:assert>
    </s:rule>
    -->

    <s:rule context="/properties/pdfimages/image">
        <!-- Images zijn gecodeerd als JPEG -->
        <s:assert test="enc = 'jpeg'">imageformaat niet gelijk aan jpeg</s:assert>
        <!-- Resolutiewaarden zijn conform eisen (binnen marge van +/- 5 ppi) -->
        <s:assert test="(x-ppi &gt; 299) and
        (x-ppi &lt; 301)">horizontale resolutie niet binnen acceptabele marges</s:assert>
        <s:assert test="(y-ppi &gt; 299) and 
        (y-ppi &lt; 301)">verticale resolutie niet binnen acceptabele marges</s:assert>
        <!-- Alle pagina's  / images zijn in kleur -->
        <s:assert test="comp = '3'">aantal kleurcomponenten niet gelijk aan 3</s:assert>
        <!-- Kleurruimte gedefinieerd d.m.v. ICC profiel -->
        <!-- LET OP: werkt niet als ICC profiel ingesloten is in JPEG! -->
        <s:assert test="color = 'icc'">kleurruimte niet gedefinieerd door ICC profiel</s:assert>

    </s:rule>

</s:pattern>
</s:schema>

