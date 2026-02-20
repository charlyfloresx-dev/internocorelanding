using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using Interno.Domain.Catalog;

namespace Interno.HealthCare.Models
{
    public class Block
    {
        [KeyAttribute]
        public int Id { get; set; }
        [RequiredAttribute]
        public Location Location { get; set; }
        [RequiredAttribute]
        [MaxLengthAttribute(45)]
        public string Code { get; set; }
        [RequiredAttribute]
        [MaxLengthAttribute(150)]
        public string Name { get; set; }
        public int Floor { get; set; }
        public virtual ICollection<Interno.Domain.Catalog.Miscellaneous> Miscellaneous { get; set; }

    }
}