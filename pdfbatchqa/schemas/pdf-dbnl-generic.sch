<?xml version="1.0"?>
<!--
   Schematron schema for DBNL PDFs: verify if PDF conforms to 
   KB requirements. 
-->
<s:schema xmlns:s="http://purl.oclc.org/dsdl/schematron">


<s:pattern>
    <s:title>Tests op eigenschappen</s:title>

    <!-- Tests op niveau PDF metadata -->
    <s:rule context="/properties/meta">
        <s:assert test="(format = 'PDF 1.7')">PDF versie is niet 1.7</s:assert>
        <s:assert test="(encryption = 'None')">PDF gebruikt versleuteling</s:assert>
    </s:rule>

    <!-- Tests op niveau PDF object -->
    <s:rule context="/properties/pages/page/image/pdf">
        <s:assert test="(filter = 'DCTDecode')">waarde filter is niet DCTDecode</s:assert>
    </s:rule>

    <!-- Tests op niveau image stream -->
    <s:rule context="/properties/pages/page/image/stream">
        <s:assert test="(format = 'JPEG')">formaat imagestream is niet JPEG</s:assert>
        <s:assert test="(jfif_density_x &gt; 299) and
        (jfif_density_x &lt; 301)">horizontale resolutie niet binnen marges</s:assert>
        <s:assert test="(jfif_density_y &gt; 299) and
        (jfif_density_y &lt; 301)">verticale resolutie niet binnen marges</s:assert>
        <s:assert test="(components = '3')">verkeerd aantal kleurkanalen</s:assert>
      </s:rule>

    <!-- Tests op gecombineerde niveaus PDF object en image stream -->
    <s:rule context="/properties/pages/page/image">
        <!-- ICC profiel kan ingesloten zijn als PDF object, in JPEG imagestream, of beide -->
        <s:assert test="(pdf/colorspace = 'ICCBased') or (stream/icc_profile)">geen ingesloten ICC profiel</s:assert>
    </s:rule>

</s:pattern>
</s:schema>

