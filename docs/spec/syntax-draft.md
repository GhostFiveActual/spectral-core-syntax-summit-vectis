# Syntax Draft

Status: exploratory and non-normative.

Example:

~~vectis
mission "Research accessibility tools" {
    source web {
        query "accessible developer tools"
    }

    analyze findings {
        require citations
    }

    when confidence >= 0.80 {
        publish report
    }

    otherwise {
        request review
    }
}
~~

This file is intentionally non-normative.

The Language Designer must produce the actual lexical and grammar
specifications before the compiler implementation treats this syntax as
authoritative.
