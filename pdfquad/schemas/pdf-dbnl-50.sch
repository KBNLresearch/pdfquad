<?xml version="1.0"?>
<!-- Schematron rules for DBNL PDFs -->

<s:schema xmlns:s="http://purl.oclc.org/dsdl/schematron">

<s:pattern>
    <s:title>DBNL profile checks</s:title>

    <!-- Checks at properties level -->
    <s:rule context="//properties">
        <!-- Check on PageMode value to ensure document doesn't open with thumbnails -->
        <s:assert test="(count(PageMode[text() = '/UseThumbs']) = 0)">PDF is set to open with thumbnails</s:assert>
        <!-- Check on PageMode value to ensure document doesn't contain file attachments -->
        <s:assert test="(count(PageMode[text() = '/UseAttachments']) = 0)">PDF contains file attachments</s:assert>
        <!-- Check on signatureFlag value to ensure document doesn't contain digital signatures -->
        <s:assert test="(count(signatureFlag[text() != -1]) = 0)">Document contains digital signatures</s:assert>
        <!-- Check on presence of JavaScript -->
        <s:assert test="(count(containsJavaScript[text() = 'True']) = 0)">Document contains JavaScript</s:assert>
        <!-- Check on open password -->
        <s:assert test="(count(openPassword[text()  = 'True']) = 0)">Document is protected with open password</s:assert>
        <!-- Check on absence of optional content -->
        <s:assert test="(count(containsOptionalContent[text() = 'True']) = 0)">PDF contains optional content</s:assert>
        <!-- Check on absence of any exceptions while parsing at pdf level -->
        <s:assert test="(count(exceptions/exception) = 0)">Parsing at PDF level resulted in one or more exceptions</s:assert>
    </s:rule>

    <!-- Checks at PDF metadata level -->
    <s:rule context="//properties/meta">
        <!-- Check on PDF version -->
        <s:assert test="(format = 'PDF 1.7')">Unexpected PDF version (expected: 1.7)</s:assert>
        <!-- Check on encryption -->
        <s:assert test="(encryption = 'None')">PDF uses encryption</s:assert>
    </s:rule>

    <!-- Checks at PDF annotations level -->
    <s:rule context="//properties/annotations">
        <!-- Check on absence of watermark annotations -->
        <s:assert test="(count(annotation[text() = '/Watermark']) = 0)">PDF contains Watermark annotation</s:assert>
        <!-- Check on absence of other unwanted annotations 
        See Table 169 (Annotation types) in ISO 32000 - 2008
        -->
        <s:assert test="(count(annotation[text() = '/Screen']) = 0)">PDF contains Screen annotation</s:assert>
        <s:assert test="(count(annotation[text() = '/Movie']) = 0)">PDF contains Movie annotation</s:assert>
        <s:assert test="(count(annotation[text() = '/3D']) = 0)">PDF contains 3D annotation</s:assert>
        <s:assert test="(count(annotation[text() = '/Sound']) = 0)">PDF contains Sound annotation</s:assert>
        <s:assert test="(count(annotation[text() = '/FileAttachment']) = 0)">PDF contains FileAttachment annotation</s:assert>
        <s:assert test="(count(annotation[text() = '/Link']) = 0)">PDF contains Link annotation</s:assert>
        <s:assert test="(count(annotation[text() = '/Ink']) = 0)">PDF contains Ink annotation</s:assert>
        <s:assert test="(count(annotation[text() = '/Popup']) = 0)">PDF contains Popup annotation</s:assert>
        <s:assert test="(count(annotation[text() = '/Widget']) = 0)">PDF contains Widget annotation</s:assert>
        <s:assert test="(count(annotation[text() = '/Polygon']) = 0)">PDF contains Polygon annotation</s:assert>
        <s:assert test="(count(annotation[text() = '/Text']) = 0)">PDF contains Text annotation</s:assert>
        <s:assert test="(count(annotation[text() = '/FreeText']) = 0)">PDF contains FreeText annotation</s:assert>
        <s:assert test="(count(annotation[text() = '/SVG']) = 0)">PDF contains SVG annotation</s:assert>
    </s:rule>

    <!-- Checks at page level -->
    <s:rule context="//properties/pages/page">
        <!-- Check on presence of only 1 image for each page -->
        <s:assert test="(count(image) = 1)">Unexpected number of images on page (expected: 1)</s:assert>
    </s:rule>

    <!-- Checks at page annotations level -->
    <s:rule context="//properties/pages/page/annotations">
        <!-- Check on absence of watermark annotations -->
        <s:assert test="(count(annotation[text() = '/Watermark']) = 0)">PDF contains Watermark annotation</s:assert>
    </s:rule>

    <!-- Checks at image level -->
    <s:rule context="//properties/pages/page/image">
        <!-- Check on presence of dict element -->
        <s:assert test="(count(dict) = 1)">Missing output element for image dictionary</s:assert>
        <!-- Check on presence of stream element -->
        <s:assert test="(count(stream) = 1)">Missing output element for image stream</s:assert>
        <!-- Check on presence of ICC profile, which can be embedded as a PDF object, in the JPEG image stream, or both -->
        <s:assert test="(dict/colorspace = 'ICCBased') or (stream/icc_profile)">Missing embedded ICC profile</s:assert>
        <!-- Consistency checks on width, height values at pdf and image stream levels -->
        <s:assert test="(dict/width = stream/width)">Width values at PDF and image stream levels are not the same</s:assert>
        <s:assert test="(dict/height = stream/height)">Height values at PDF and image stream levels are not the same</s:assert>
        <!-- Consistency check on bpc values at pdf and image stream levels -->
        <s:assert test="(dict/bpc = stream/bpc)">Bit per component values at PDF and image stream levels are not the same</s:assert>
    </s:rule>

    <!-- Checks at image dictionary level -->
    <s:rule context="//properties/pages/page/image/dict">
        <!-- Check on expected filter value for JPEG encoded image data -->
        <s:assert test="(filter = 'DCTDecode')">Unexpected filter value (expected: DCTDecode)</s:assert>
    </s:rule>

    <!-- Checks at image stream level -->
    <s:rule context="//properties/pages/page/image/stream">
        <!-- Check on expected format of the image stream -->
        <s:assert test="(format = 'JPEG')">Unexpected image stream format (expected: JPEG)</s:assert>
        <!-- Check on horizontal and vertical resolution (with tolerance of +/- 1 ppi) -->
        <s:assert test="(jfif_density_x &gt;= 299) and
        (jfif_density_x &lt;= 301)">Horizontal resolution outside permitted range</s:assert>
        <s:assert test="(jfif_density_y &gt;= 299) and
        (jfif_density_y &lt;= 301)">Vertical resolution outside permitted range</s:assert>
        <!-- Check on expected number of color components -->
        <s:assert test="(components = '3')">Unexpected number of color components (expected: 3)</s:assert>
        <!-- Check on JPEG compression quality level (with tolerance of +/- 2 levels) -->
        <s:assert test="(JPEGQuality &gt;= 48) and
        (JPEGQuality &lt;= 52)">JPEG compression quality outside permitted range</s:assert>
        <!-- Check on absence of any exceptions while parsing the image stream -->
        <s:assert test="(count(exceptions/exception) = 0)">Properties extraction at stream level resulted in one or more exceptions</s:assert>
    </s:rule>

</s:pattern>
</s:schema>
